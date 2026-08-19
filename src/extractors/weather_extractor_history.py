"""Extractor for pulling 60days historical rainfall data."""
import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
# save to data/raw for future use


def save_raw_historical_data(raw_records):
    output_path = Path(__file__).parent.parent.parent / "data" / \
        "raw" / "raw_historical_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_records, f, indent=4, default=str)
        print(f"OOO Successfully saved raw historical data to {output_path}")
    except Exception as e:
        print(f"XXX Error saving raw historical data: {e}")


# Load environment variables from .env
load_dotenv()
WEATHER_API_URL = os.getenv("WEATHER_API_URL")


def fetch_historical_weather_data(days_back: int = 60):
    """Fetches real historical rainfall data per station/area for past days using WEATHER_API_URL."""
    if not WEATHER_API_URL:
        print("XXX Error: WEATHER_API_URL is not set in the .env file.")
        return []

    print(
        f"Fetching historical weather data with area names for the past {days_back} days...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    historical_records = []
    station_names_cache = {}  # Cache to store stationId -> stationName mapping

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        separator = "&" if "?" in WEATHER_API_URL else "?"
        url = f"{WEATHER_API_URL}{separator}date={date_str}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("code") == 0:
                    data_block = json_data.get("data", {})

                    # 1. Build station ID to name map if available in metadata
                    stations_meta = data_block.get("stations", [])
                    for station in stations_meta:
                        s_id = station.get("id") or station.get("device_id")
                        s_name = station.get("name") or station.get("area")
                        if s_id and s_name:
                            station_names_cache[s_id] = s_name

                    readings = data_block.get("readings", [])

                    # 2. Aggregate daily total rainfall per station
                    station_daily_totals = {}
                    for reading in readings:
                        stations_data = reading.get("data", [])
                        for station in stations_data:
                            s_id = station.get("stationId")
                            val = station.get("value", 0.0)

                            if val is not None:
                                if s_id not in station_daily_totals:
                                    station_daily_totals[s_id] = {
                                        "name": station_names_cache.get(s_id, f"Station-{s_id}"),
                                        "total": 0.0
                                    }
                                station_daily_totals[s_id]["total"] += float(
                                    val)

                    # 3. Format into records per area/station per date
                    for s_id, info in station_daily_totals.items():
                        historical_records.append({
                            "area_name": info["name"],
                            "record_date": date_str,
                            "total_rainfall_mm": round(info["total"], 2)
                        })

        except requests.exceptions.RequestException as e:
            print(f"XXX  Warning: Failed to fetch data for {date_str}: {e}")

        current_date += timedelta(days=1)

    print(
        f"OOO Successfully fetched {len(historical_records)} station-level weather records.")
    return historical_records


if __name__ == "__main__":
    print("Testing Historical Weather Extractor...")
    data = fetch_historical_weather_data(60)
    if data:
        print(
            f"OOO Success! Fetched {len(data)} historical weather records for the past 60 days."
        )
        save_raw_historical_data(data)
    else:
        print("XXX Test failed: No historical data returned.")
    print(data[:3])
