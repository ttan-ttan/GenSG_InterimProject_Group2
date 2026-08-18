"""Transformer for 2-hour weather forecasts and check rain status."""

from datetime import datetime

# Conditions that indicate rain or showers
RAIN_CONDITIONS = [
    "Light Rain", "Moderate Rain", "Heavy Rain",
    "Passing Showers", "Light Showers", "Showers", "Heavy Showers",
    "Thundery Showers", "Heavy Thundery Showers",
    "Heavy Thundery Showers with Gusty Winds"
]

# helper function to check if extracted string got rain condition keyword


def check_rain_forecast(forecast_string: str) -> bool:
    return any(condition.lower() in forecast_string.lower() for condition in RAIN_CONDITIONS)

# CREATE TABLE weather_forecast (
#     id SERIAL PRIMARY KEY,
#     area_name VARCHAR(100) NOT NULL UNIQUE,
#     forecast_text VARCHAR(100) NOT NULL,
#     will_rain BOOLEAN NOT NULL,
#     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );
# main transform to check data exist, putting it into schema corectly


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
        forecast_text = entry.get("forecast")
        will_rain = check_rain_forecast(forecast_text)

        transformed_records.append({
            "area_name": area,
            "forecast_text": forecast_text,
            "will_rain": will_rain,
            "updated_at": update_timestamp
        })

    print(
        f"OOO Successfully transformed {len(transformed_records)} forecast records.")
    return transformed_records
