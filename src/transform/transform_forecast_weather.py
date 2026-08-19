"""Transformer for 2-hour weather forecasts and check rain status."""

from datetime import datetime

RAIN_CONDITIONS = [
    "Light Rain", "Moderate Rain", "Heavy Rain",
    "Passing Showers", "Light Showers", "Showers", "Heavy Showers",
    "Thundery Showers", "Heavy Thundery Showers",
    "Heavy Thundery Showers with Gusty Winds"
]


def get_postal_prefix_from_area(area_name: str) -> str:
    """Maps forecast area names to their corresponding Singapore postal prefix/district."""
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


def check_rain_forecast(forecast_string: str) -> bool:
    return any(condition.lower() in forecast_string.lower() for condition in RAIN_CONDITIONS)


def transform_two_hour_forecast(raw_data):
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
        postal_prefix = get_postal_prefix_from_area(area)
        forecast_text = entry.get("forecast")
        will_rain = check_rain_forecast(forecast_text)

        transformed_records.append({
            "area_name": area,
            "postal_prefix": postal_prefix,
            "forecast_text": forecast_text,
            "will_rain": will_rain,
            "updated_at": update_timestamp
        })

    print(
        f"OOO Successfully transformed {len(transformed_records)} forecast records.")
    return transformed_records
