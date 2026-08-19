"""Transformation logic for real-time weather payloads."""

from datetime import datetime


def get_postal_prefix_from_area(area_name: str) -> str:
    """Maps weather station area names to their corresponding Singapore postal prefix/district."""
    if not area_name:
        return "Unknown"

    mapping = {
        "Ang Mo Kio": "D20",
        "Bishan": "D20",
        "Clementi": "D05",
        "West Coast": "D05",
        "Bedok": "D16",
        "Changi": "D17",
        "Jurong": "D22",
        "Yishun": "D27",
        "Woodlands": "D25"
    }

    for key, prefix in mapping.items():
        if key.lower() in area_name.lower():
            return prefix

    return "D01"


def transform_real_time_weather(raw_payload):
    """Transforms a single real-time snapshot payload into database-ready rows."""
    if not raw_payload or "data" not in raw_payload:
        return []

    data_container = raw_payload["data"]
    stations = data_container.get("stations", [])
    readings = data_container.get("readings", [])

    station_name_map = {station["id"]: station["name"] for station in stations}
    transformed_records = []

    for reading_entry in readings:
        timestamp_str = reading_entry.get("timestamp")
        try:
            recorded_at = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            recorded_at = datetime.now()

        for item in reading_entry.get("data", []):
            station_id = item.get("stationId")
            rainfall_value = item.get("value", 0.0)
            area_name = station_name_map.get(station_id, "Unknown Area")
            postal_prefix = get_postal_prefix_from_area(area_name)
            is_heavy_rain = bool(rainfall_value >= 10.0)

            transformed_records.append({
                "area_name": area_name,
                "postal_prefix": postal_prefix,
                "reading_value": rainfall_value,
                "is_heavy_rain": is_heavy_rain,
                "recorded_at": recorded_at,
            })

    return transformed_records
