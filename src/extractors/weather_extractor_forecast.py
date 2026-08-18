"""Extractor module for pulling the 2-hour weather forecast from NEA."""

import requests


def fetch_two_hour_forecast():
    """Fetches the latest 2-hour weather forecast from data.gov.sg."""
    url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
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
        print("Successfully fetched 2-hour forecast sample data.")
