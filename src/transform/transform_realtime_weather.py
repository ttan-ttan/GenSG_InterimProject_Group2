"""Transformation logic for real-time weather payloads."""

from datetime import datetime


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
            is_heavy_rain = bool(rainfall_value >= 10.0)

            transformed_records.append({
                "area_name": area_name,
                "reading_value": rainfall_value,
                "is_heavy_rain": is_heavy_rain,
                "recorded_at": recorded_at,
            })

    return transformed_records
