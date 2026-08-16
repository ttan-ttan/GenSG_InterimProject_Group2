"""Extractor specifically for real-time live rainfall data from data.gov.sg."""

import os
from dotenv import load_dotenv
import requests

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
    else:
        print("XXX Test failed: No real-time data returned.")
