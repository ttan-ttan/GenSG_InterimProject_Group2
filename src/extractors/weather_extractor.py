"""Extractor module for real-time and historical rainfall data from data.gov.sg."""

from datetime import datetime, timedelta
import os
import time
from dotenv import load_dotenv
import requests


# Load environment variables from the .env file in the root directory
load_dotenv()

# Fetch the API URL securely from the environment variables
WEATHER_API_URL = os.getenv("WEATHER_API_URL")


def fetch_real_time_weather():
    """Extracts real-time weather data from data.gov.sg."""
    if not WEATHER_API_URL:
        print("XXX Error: WEATHER_API_URL is not set in the .env file.")
        return None

    response = requests.get(WEATHER_API_URL, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"XXX Error fetching real-time weather: {response.status_code}")
        return None


def fetch_historical_weather(days_back=14):
    """Extracts past X days of weather records day-by-day using the date parameter."""
    if not WEATHER_API_URL:
        print(" Error: WEATHER_API_URL is not set in the .env file.")
        return []

    historical_responses = []
    today = datetime.now()

    for i in range(1, days_back + 1):
        target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        params = {"date": target_date}

        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            historical_responses.append(
                {"date": target_date, "data": response.json()})
        else:
            print(
                f"XXX Failed to fetch data for {target_date}: {response.status_code}"
            )
    # add 1s to prevent API rate limit
    time.sleep(1.0)

    return historical_responses


# For testing purposes
if __name__ == "__main__":
    print("Testing realtime Extractor...")
    data = fetch_real_time_weather()

    if data:
        actual_data = data.get("data", {})
        stations = actual_data.get("stations", [])
        readings = actual_data.get("readings", [])
        print(
            f"OOO Success! Fetched {len(stations)} stations and {len(readings)}"
            " reading entries."
        )
        if stations:
            print("Sample Station:", stations[0])
    else:
        print("XXX Test failed: No real-time data returned.")

    print("\nTesting 14-days Extractor...")
    hist_data = fetch_historical_weather(days_back=14)

    if hist_data:
        print(
            f"OOO Success! Fetched historical records for {len(hist_data)} days."
        )
        if hist_data[0].get("data"):
            print("Sample Day Data:", hist_data[0]["date"])
    else:
        print("XXX Test failed: No historical data returned.")
