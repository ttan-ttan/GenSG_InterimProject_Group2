"""Transformer module for parsing 2-hour weather forecasts and determining rain status."""

from datetime import datetime

# Conditions that indicate rain or showers
RAIN_CONDITIONS = [
    "Light Rain", "Moderate Rain", "Heavy Rain",
    "Passing Showers", "Light Showers", "Showers", "Heavy Showers",
    "Thundery Showers", "Heavy Thundery Showers",
    "Heavy Thundery Showers with Gusty Winds"
]


def parse_rain_forecast(forecast_string: str) -> bool:
    """Returns True if the forecast condition indicates rain, otherwise False."""
    return any(condition.lower() in forecast_string.lower() for condition in RAIN_CONDITIONS)


def transform_two_hour_forecast(raw_data):
    """Parses raw 2-hour forecast JSON data into clean records for database insertion."""
    if not raw_data or "items" not in raw_data:
        print("XXX Warning: Raw forecast data is empty or invalid.")
        return []

    transformed_records = []
    items = raw_data.get("items", [])

    if not items:
        return []

    latest_item = items[0]
    update_timestamp = latest_item.get(
        "update_timestamp", datetime.now().isoformat())
    forecasts = latest_item.get("forecasts", [])

    for entry in forecasts:
        area = entry.get("area")
        forecast_text = entry.get("forecast")
        will_rain = parse_rain_forecast(forecast_text)

        transformed_records.append({
            "area_name": area,
            "forecast_text": forecast_text,
            "will_rain": will_rain,
            "updated_at": update_timestamp
        })

    print(
        f"Successfully transformed {len(transformed_records)} forecast records.")
    return transformed_records
