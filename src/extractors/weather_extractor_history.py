"""Extractor module for pulling actual historical rainfall data from data.gov.sg."""

from datetime import datetime, timedelta
import requests


def fetch_historical_weather_data(days_back: int = 30):
    """Fetches real historical rainfall data for past days from data.gov.sg."""
    print(f"Fetching historical weather data for the past {days_back} days...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    historical_records_map = {}

    # Loop through each day in the date range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"https://api-open.data.gov.sg/v2/real-time/api/rainfall?date={date_str}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("code") == 0:
                    readings = json_data.get("data", {}).get("readings", [])

                    # Sum up daily rainfall across stations or take an average for that day
                    daily_total = 0.0
                    count = 0
                    for reading in readings:
                        stations_data = reading.get("data", [])
                        for station in stations_data:
                            val = station.get("value", 0.0)
                            if val is not None:
                                daily_total += float(val)
                                count += 1

                    # Calculate average or total across reporting stations for that day
                    avg_daily_rain = round(
                        daily_total / count, 2) if count > 0 else 0.0

                    historical_records_map[date_str] = avg_daily_rain
                else:
                    historical_records_map[date_str] = 0.0
            else:
                historical_records_map[date_str] = 0.0
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch data for {date_str}: {e}")
            historical_records_map[date_str] = 0.0

        current_date += timedelta(days=1)

    # Format into list of dicts for the transformer
    historical_records = [
        {"record_date": d, "total_rainfall_mm": rain}
        for d, rain in historical_records_map.items()
    ]

    print(
        f"Successfully fetched {len(historical_records)} days of historical weather data.")
    return historical_records


if __name__ == "__main__":
    data = fetch_historical_weather_data(14)
    print(data[:3])
