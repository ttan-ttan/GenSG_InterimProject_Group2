"""Derive Singapore postal codes for dengue clusters using the OneMap APIs.

Reads an NEA dengue cluster GeoJSON file and resolves a postal code for every
cluster in two passes:

1. Search API - the LOCALITY string is parsed into address queries. Localities
   naming a block ("Senja Cl (Blk 647A, 647B)") resolve to exact addresses.
2. Reverse Geocode API - localities naming only roads have no postal code of
   their own, so the cluster polygon is sampled and the buildings inside it are
   looked up instead, keeping those on the roads the locality names.

Usage:
    python src/geocode.py "path/to/DengueClustersGEOJSON.geojson"
    python src/geocode.py "path/to/clusters.geojson" -o data/processed/postal_codes.csv
"""

import argparse
import csv
import json
import os
import re
import time
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = "https://www.onemap.gov.sg/api/common/elastic/search"
REVGEOCODE_URL = "https://www.onemap.gov.sg/api/public/revgeocode"

# NEA writes localities like "Senja Cl (Blk 647A, 647B)" or
# "Lilac Dr, Walk / Mimosa Cres, Rd (Mimosa Pk)". A trailing bracket holds
# either a list of block numbers or the name of a building/estate.
PAREN_RE = re.compile(r"^(?P<road>.*?)\s*\((?P<paren>[^)]*)\)\s*$")
BLK_RE = re.compile(r"^blk\b", re.IGNORECASE)

# OneMap returns the string "NIL" in POSTAL for roads that have no single
# postal code of their own.
NO_POSTAL = "NIL"

# OneMap stores addresses in full, while NEA abbreviates. Expanding the query
# lets us confirm a result really belongs to the road we asked for, because the
# search is fuzzy enough to return unrelated addresses for a loose match.
ABBREVIATIONS = {
    "AVE": "AVENUE", "BLK": "BLOCK", "BT": "BUKIT", "CL": "CLOSE", "CRES": "CRESCENT",
    "CTR": "CENTRE", "CTRL": "CENTRAL", "DR": "DRIVE", "GDN": "GARDEN",
    "GDNS": "GARDENS", "GR": "GROVE", "HTS": "HEIGHTS", "IND": "INDUSTRIAL",
    "JLN": "JALAN", "KG": "KAMPONG", "LK": "LINK", "LN": "LANE", "LOR": "LORONG",
    "MKT": "MARKET", "NTH": "NORTH", "PK": "PARK", "PL": "PLACE", "RD": "ROAD",
    "SQ": "SQUARE", "ST": "STREET", "STH": "SOUTH", "TER": "TERRACE",
    "TG": "TANJONG", "TWR": "TOWER", "UPP": "UPPER",
}

_search_cache: Dict[str, List[dict]] = {}


def _token() -> str:
    token = os.getenv("ONEMAP_TOKEN")
    if not token:
        raise RuntimeError("ONEMAP_TOKEN is not set in the environment (.env file).")
    return token


def _get(url: str, params: dict) -> dict:
    """GET a OneMap endpoint, backing off when the rate limit is hit."""
    for attempt in range(3):
        response = requests.get(url, params=params, headers={"Authorization": _token()})
        if response.status_code == 429:  # API limit exceeded
            time.sleep(2 * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"OneMap rate limit hit repeatedly calling {url}.")


# --------------------------------------------------------------------------
# Pass 1: the Search API, driven by the LOCALITY text
# --------------------------------------------------------------------------


def onemap_search(search_val: str) -> List[dict]:
    """Return the first page of OneMap search results, cached in memory."""
    if search_val not in _search_cache:
        _search_cache[search_val] = _get(
            SEARCH_URL,
            {
                "searchVal": search_val,
                "returnGeom": "N",
                "getAddrDetails": "Y",
                "pageNum": 1,
            },
        ).get("results", [])
    return _search_cache[search_val]


def get_postal_code(search_val: str) -> Optional[str]:
    """Return the postal code of the best-matching result, or None if there is none.

    search_val can be a building name, road name, bus stop number, or postal code.
    Note that a bare road name has no postal code of its own, so this returns None.
    """
    results = onemap_search(search_val)
    if not results:
        return None
    postal = results[0].get("POSTAL")
    return None if postal == NO_POSTAL else postal


def expand_roads(road_text: str) -> List[str]:
    """Expand NEA's comma shorthand into full road names.

    NEA abbreviates a shared road prefix, so "Luxus Hill Ave, Dr, View" means
    Luxus Hill Ave, Luxus Hill Dr and Luxus Hill View. The prefix is everything
    in the first entry except its last word.
    """
    parts = [p.strip() for p in road_text.split(",") if p.strip()]
    if not parts:
        return []

    first = parts[0]
    base = " ".join(first.split()[:-1])
    roads = [first]
    for suffix in parts[1:]:
        roads.append(f"{base} {suffix}" if base else suffix)
    return roads


def parse_locality(locality: str) -> List[Tuple[str, str]]:
    """Turn one LOCALITY string into (query, kind) pairs to send to OneMap.

    kind is "block" (road with a block number, resolves to one postal code),
    "building" (a named building or estate) or "road" (a road on its own).
    """
    queries: List[Tuple[str, str]] = []

    for segment in locality.split("/"):
        segment = segment.strip()
        if not segment:
            continue

        match = PAREN_RE.match(segment)
        if match:
            road_text, paren = match.group("road"), match.group("paren").strip()
        else:
            road_text, paren = segment, None

        roads = expand_roads(road_text)

        if paren and BLK_RE.match(paren):
            # A block number plus a road resolves to exactly one address, so
            # search "647A Senja Cl" rather than the road on its own.
            blocks = [b.strip() for b in BLK_RE.sub("", paren).split(",") if b.strip()]
            queries.extend(
                (f"{block} {road}", "block") for road in roads for block in blocks
            )
        else:
            if paren:
                queries.append((paren, "building"))
            queries.extend((road, "road") for road in roads)

    # Preserve order while dropping repeats (e.g. "Nim Rd" listed twice).
    seen = set()
    unique = []
    for query in queries:
        if query not in seen:
            seen.add(query)
            unique.append(query)
    return unique


def expand_abbreviations(text: str) -> str:
    """Expand NEA's road abbreviations, e.g. 'Jln Kayu' -> 'JALAN KAYU'."""
    return " ".join(ABBREVIATIONS.get(w.upper(), w.upper()) for w in text.split())


def locality_roads(locality: str) -> List[str]:
    """Return the expanded road names a locality mentions, for matching results."""
    roads = set()
    for query, kind in parse_locality(locality):
        expanded = expand_abbreviations(query)
        if kind == "block":
            # Drop the leading block number, leaving the road itself.
            expanded = " ".join(expanded.split()[1:])
        roads.add(expanded)
    return sorted(roads)


def result_matches_query(query: str, result: dict) -> bool:
    """Check that a search result actually belongs to the place we asked for.

    OneMap's search is fuzzy, so a query can return an address on an unrelated
    road. Requiring the expanded query to appear in the returned address keeps
    those out. Block queries are also accepted on the road alone, since the
    block number may be recorded separately from the street.
    """
    address = result.get("ADDRESS", "").upper()
    if not address:
        return False

    expanded = expand_abbreviations(query)
    if expanded in address:
        return True

    words = expanded.split()
    return len(words) > 1 and " ".join(words[1:]) in address


def resolve_locality(locality: str) -> List[dict]:
    """Look up every query derived from a locality and return one row each."""
    rows = []
    for query, kind in parse_locality(locality):
        results = onemap_search(query)
        top = results[0] if results else {}
        postal = top.get("POSTAL")
        verified = bool(top) and result_matches_query(query, top)
        if postal in (None, NO_POSTAL) or not verified:
            postal = ""
        rows.append(
            {
                "SOURCE": "locality",
                "QUERY": query,
                "QUERY_TYPE": kind,
                "POSTAL": postal,
                "VERIFIED": "Y" if verified else "N",
                "ADDRESS": top.get("ADDRESS", ""),
                "BLK_NO": top.get("BLK_NO", ""),
                "ROAD_NAME": top.get("ROAD_NAME", ""),
                "BUILDING": top.get("BUILDING", ""),
                "LATITUDE": top.get("LATITUDE", ""),
                "LONGITUDE": top.get("LONGITUDE", ""),
                "MATCH_COUNT": len(results),
            }
        )
    return rows


# --------------------------------------------------------------------------
# Pass 2: the Reverse Geocode API, driven by the cluster polygon
# --------------------------------------------------------------------------


def reverse_geocode(lat: float, lon: float, buffer_m: int = 500) -> List[dict]:
    """Return up to 10 buildings within buffer_m metres of a point."""
    return _get(
        REVGEOCODE_URL,
        {"location": f"{lat},{lon}", "buffer": buffer_m, "addressType": "All"},
    ).get("GeocodeInfo", [])


def _rings(geometry: dict) -> List[List[List[float]]]:
    """Return every coordinate ring of a Polygon or MultiPolygon."""
    if geometry.get("type") == "Polygon":
        return geometry.get("coordinates", [])
    rings = []
    for polygon in geometry.get("coordinates", []):
        rings.extend(polygon)
    return rings


def ring_centroid(ring: List[List[float]]) -> Tuple[float, float]:
    """Return the area-weighted centroid of a ring as (lon, lat)."""
    area = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    if area == 0:  # degenerate ring, fall back to the mean of its points
        return (
            sum(p[0] for p in ring) / len(ring),
            sum(p[1] for p in ring) / len(ring),
        )

    area *= 0.5
    return cx / (6 * area), cy / (6 * area)


def sample_points(geometry: dict, max_points: int) -> List[Tuple[float, float]]:
    """Return (lat, lon) probes covering a cluster: its centroid, then vertices.

    A cluster can be far wider than the 500m reverse-geocode buffer, and a
    concave polygon can even put its centroid outside itself, so vertices are
    sampled too.
    """
    rings = [r for r in _rings(geometry) if len(r) >= 3]
    if not rings:
        return []

    biggest = max(rings, key=len)
    lon, lat = ring_centroid(biggest)
    points = [(lat, lon)]

    remaining = max_points - 1
    if remaining > 0:
        step = max(1, len(biggest) // remaining)
        for vertex in biggest[::step][:remaining]:
            points.append((vertex[1], vertex[0]))
    return points


def resolve_geometry(geometry: dict, roads: Iterable[str], max_points: int) -> List[dict]:
    """Find buildings inside a cluster polygon, preferring its named roads.

    Buildings on a road the locality names are returned when there are any;
    otherwise every building found is returned, flagged as unverified, since
    the cluster's own roads could not confirm them.
    """
    road_set = set(roads)
    on_named_road: Dict[str, dict] = {}
    nearby: Dict[str, dict] = {}

    for lat, lon in sample_points(geometry, max_points):
        for building in reverse_geocode(lat, lon):
            postal = building.get("POSTALCODE", "")
            if not postal or postal == NO_POSTAL:
                continue

            road = (building.get("ROAD") or "").upper()
            name = (building.get("BUILDINGNAME") or "").upper()
            block = building.get("BLOCK") or ""
            address = " ".join(x for x in (block, road, name) if x and x != "NULL")

            row = {
                "SOURCE": "geometry",
                "QUERY": f"{lat:.6f},{lon:.6f}",
                "QUERY_TYPE": "reverse_geocode",
                "POSTAL": postal,
                "ADDRESS": address,
                "BLK_NO": block,
                "ROAD_NAME": road,
                "BUILDING": building.get("BUILDINGNAME", ""),
                "LATITUDE": building.get("LATITUDE", ""),
                "LONGITUDE": building.get("LONGITUDE", ""),
                "MATCH_COUNT": 1,
            }

            if road in road_set:
                row["VERIFIED"] = "Y"
                on_named_road.setdefault(postal, row)
            else:
                row["VERIFIED"] = "N"
                nearby.setdefault(postal, row)

    chosen = on_named_road or nearby
    return sorted(chosen.values(), key=lambda r: r["POSTAL"])


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

FIELDNAMES = [
    "OBJECTID",
    "LOCALITY",
    "CASE_SIZE",
    "SOURCE",
    "QUERY",
    "QUERY_TYPE",
    "POSTAL",
    "VERIFIED",
    "ADDRESS",
    "BLK_NO",
    "ROAD_NAME",
    "BUILDING",
    "LATITUDE",
    "LONGITUDE",
    "MATCH_COUNT",
]


def load_features(geojson_path: str) -> List[dict]:
    with open(geojson_path, encoding="utf-8") as f:
        return json.load(f).get("features", [])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geojson", help="Path to the NEA dengue cluster GeoJSON file.")
    parser.add_argument(
        "-o",
        "--output",
        default="data/processed/dengue_cluster_postal_codes.csv",
        help="Where to write the CSV of results.",
    )
    parser.add_argument(
        "--geom-points",
        type=int,
        default=5,
        help="Polygon probes per cluster when falling back to reverse geocoding.",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Skip reverse geocoding and report only what the LOCALITY text gives.",
    )
    args = parser.parse_args()

    features = load_features(args.geojson)
    print(f"Loaded {len(features)} dengue clusters from {args.geojson}\n")

    rows = []
    covered = 0
    for feature in features:
        properties = feature.get("properties", {})
        locality = (properties.get("LOCALITY") or "").strip()
        if not locality:
            continue

        resolved = resolve_locality(locality)
        found = sum(1 for row in resolved if row["POSTAL"])
        note = f"{found} from locality"

        if not found and not args.no_fallback:
            fallback = resolve_geometry(
                feature.get("geometry", {}), locality_roads(locality), args.geom_points
            )
            resolved.extend(fallback)
            found = len(fallback)
            note = f"{found} from polygon (reverse geocode)"

        covered += bool(found)
        print(f"  {locality[:58]:58s} {note}")

        for row in resolved:
            rows.append(
                {
                    "OBJECTID": properties.get("OBJECTID", ""),
                    "LOCALITY": locality,
                    "CASE_SIZE": properties.get("CASE_SIZE", ""),
                    **row,
                }
            )

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    with_postal = [row for row in rows if row["POSTAL"]]
    print(f"\nWrote {len(rows)} rows to {args.output}")
    print(f"{len(with_postal)} rows carry a postal code "
          f"({len({row['POSTAL'] for row in with_postal})} distinct).")
    print(f"{covered} of {len(features)} clusters resolved to at least one postal code.")


if __name__ == "__main__":
    main()
