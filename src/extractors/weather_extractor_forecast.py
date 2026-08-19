"""Extractor for 2-hour weather forecast from NEA API."""

from pathlib import Path
import json
import requests
import os
from dotenv import load_dotenv

# save to data/raw for future use


def save_raw_forecast_data(raw_records):
    output_path = Path(__file__).parent.parent.parent / "data" / \
        "raw" / "raw_forecast_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_records, f, indent=4, default=str)
        print(f"OOO Successfully saved raw forecast data to {output_path}")
    except Exception as e:
        print(f"XXX Error saving raw forecast data: {e}")


# Load environment variables from .env
load_dotenv()
WEATHER_FORECAST_API_URL = os.getenv("WEATHER_FORECAST_API_URL")

# main function fetch 2hr data


def fetch_two_hour_forecast():
    """Fetches the latest 2-hour weather forecast from data.gov.sg."""
    url = WEATHER_FORECAST_API_URL
    print("Fetching 2-hour weather forecast data...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        json_data = response.json()

        if json_data.get("code") != 0:
            print(f"XXX API Error: {json_data.get('errorMsg')}")
            return None

        return json_data.get("data", {})

    except requests.exceptions.RequestException as e:
        print(f"XXX Request failed: {e}")
        return None


if __name__ == "__main__":
    data = fetch_two_hour_forecast()
    if data:
        print("OOO Successfully fetched 2-hour forecast sample data.")
        save_raw_forecast_data(data)
