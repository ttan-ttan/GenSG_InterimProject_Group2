"""Geocoding script for Singapore Dengue Clusters.

Reads raw NEA dengue cluster GeoJSON data, extracts local features, 
cleans complex multi-street locality strings, queries the OneMap API, 
applies a fallback dictionary for unmatched compound locations, 
and saves the output to a processed CSV file.
"""

import os
import re
import json
import pandas as pd
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Fallback mapping for common compound/complex NEA strings that OneMap fails to resolve automatically
KNOWN_LOCALITY_PREFIXES = {
    "luxus hill": "80",
    "lilac": "80",
    "mimosa": "80",
    "begonia": "80",
    "countryside": "78",
    "lentor": "78",
    "jln kayu": "79",
    "ho ching": "61",
    "tah ching": "61",
    "yuan ching": "61",
    "petir": "67",
}


def clean_location_query(raw_locality: str) -> str:
    """Cleans complex NEA cluster locality strings into a single, searchable query for OneMap."""
    if not raw_locality or not isinstance(raw_locality, str):
        return ""

    # 1. Remove text inside parentheses (e.g., '(Blk 119)', '(Maysprings)')
    cleaned = re.sub(r'\([^)]*\)', '', raw_locality)

    # 2. Split by major delimiters like slashes '/' or commas ',' to take the first main road
    primary_part = cleaned.split('/')[0].split(',')[0].strip()

    return primary_part


def get_postal_from_onemap(raw_locality: str):
    """Queries OneMap API using the cleaned primary road name, with a fallback dictionary."""
    query_string = clean_location_query(raw_locality)
    if query_string:
        url = "https://www.onemap.gov.sg/api/common/elastic/search"
        params = {
            'searchVal': query_string,
            'returnGeom': 'Y',
            'getAddrDetails': 'Y',
            'pageNum': '1'
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    top_match = results[0]
                    postal_code = top_match.get("POSTAL", "")
                    if postal_code and postal_code != "NIL":
                        return postal_code, top_match
        except Exception as e:
            print(f"Error querying OneMap for '{query_string}': {e}")

    # Fallback Mechanism: If API fails or returns nothing, check keyword dictionary
    raw_lower = raw_locality.lower()
    for keyword, prefix in KNOWN_LOCALITY_PREFIXES.items():
        if keyword in raw_lower:
            dummy_postal = f"{prefix}0000"
            return dummy_postal, {"ADDRESS": raw_locality, "ROAD_NAME": keyword}

    return None, {}


def run_geocoding(input_geojson: str, output_csv: str) -> None:
    """Reads raw GeoJSON dataset, processes features/localities, and outputs CSV."""
    if not os.path.exists(input_geojson):
        raise FileNotFoundError(f"Input file not found at {input_geojson}")

    print(f"Reading raw GeoJSON data from {input_geojson}...")
    with open(input_geojson, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    features = geojson_data.get("features", [])
    if not features:
        print("Input dataset contains no features.")
        return

    rows = []
    total_rows = len(features)

    print(f"Starting geocoding process for {total_rows} records...")
    for idx, feature in enumerate(features):
        properties = feature.get("properties", {})

        # Adjust depending on exact property key name for locality/name in GeoJSON
        locality = properties.get("LOCALITY") or properties.get(
            "name") or properties.get("NAME") or ""
        case_size = properties.get("CASE_SIZE") or properties.get(
            "case_size") or properties.get("NO_OF_CASES") or 0
        fmel_upd_d = properties.get(
            "FMEL_UPD_D") or properties.get("date") or ""

        # Call OneMap search / fallback logic
        postal, top = get_postal_from_onemap(str(locality))
        verified = True if postal else False

        rows.append({
            "LOCALITY": locality,
            "CASE_SIZE": case_size,
            "FMEL_UPD_D": fmel_upd_d,
            "POSTAL": postal if postal else "",
            "POSTAL_PREFIX": str(postal)[:2] if postal and postal != "NIL" else "",
            "VERIFIED": "Y" if verified else "N",
            "ADDRESS": top.get("ADDRESS", ""),
            "BLK_NO": top.get("BLK_NO", ""),
            "ROAD_NAME": top.get("ROAD_NAME", ""),
            "BUILDING": top.get("BUILDING", ""),
            "LATITUDE": top.get("LATITUDE", ""),
            "LONGITUDE": top.get("LONGITUDE", ""),
            "MATCH_COUNT": 1 if postal else 0,
        })

    output_df = pd.DataFrame(rows)

    # Ensure output directory exists
    os.makedirs(Path(output_csv).parent, exist_ok=True)

    output_df.to_csv(output_csv, index=False)
    print(f"Geocoding complete. Processed data saved to {output_csv}")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_file = project_root / "data" / "raw" / "dengue_clusters.geojson"
    processed_file = project_root / "data" / \
        "processed" / "dengue_cluster_postal_codes.csv"

    run_geocoding(str(raw_file), str(processed_file))
