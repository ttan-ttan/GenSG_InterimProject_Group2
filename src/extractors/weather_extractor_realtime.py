"""Extractor specifically for real-time live rainfall data."""
import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import json


def save_raw_realtime_data(raw_records):
    """Saves the raw real-time data to a JSON file for debugging and record-keeping."""
    output_path = Path(__file__).parent.parent.parent / "data" / \
        "raw" / "raw_realtime_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_records, f, indent=4, default=str)
        print(f"OOO Successfully saved raw real-time data to {output_path}")
    except Exception as e:
        print(f"XXX Error saving raw real-time data: {e}")


load_dotenv()
WEATHER_API_URL = os.getenv("WEATHER_API_URL")


def fetch_real_time_weather():
    """Extracts the latest real-time rainfall data snapshot."""
    if not WEATHER_API_URL:
        print("XXX Error: WEATHER_API_URL is not set in the .env file.")
        return None

    try:
        response = requests.get(WEATHER_API_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"XXX Error fetching real-time weather: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"XXX Network error fetching real-time weather: {e}")
        return None


if __name__ == "__main__":
    print("Testing Real-Time Extractor...")
    data = fetch_real_time_weather()
    if data:
        actual_data = data.get("data", {})
        stations = actual_data.get("stations", [])
        readings = actual_data.get("readings", [])
        print(
            f"OOO Success! Fetched {len(stations)} stations and {len(readings)} reading entries.")
        save_raw_realtime_data(data)
    else:
        print("XXX Test failed: No real-time data returned.")
