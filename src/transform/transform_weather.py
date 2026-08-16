"""Transform module for parsing weather data into structured DataFrames."""

import pandas as pd


def transform_weather_data(raw_data_json, record_type="realtime"):
    """Transforms raw weather API JSON into a flat Pandas DataFrame."""
    if not raw_data_json:
        return pd.DataFrame()

    records = []

    # Handle data structure from data.gov.sg v2 API
    data_block = raw_data_json.get("data", {})
    stations = data_block.get("stations", [])
    readings = data_block.get("readings", [])

    # Create a lookup map for station details
    station_map = {s.get("id"): s for s in stations}

    for reading in readings:
        timestamp = reading.get("timestamp")
        for entry in reading.get("data", []):
            station_id = entry.get("stationId")
            station_info = station_map.get(station_id, {})

            records.append({
                "station_id": station_id,
                "station_name": station_info.get("name"),
                "latitude": station_info.get("location", {}).get("latitude"),
                "longitude": station_info.get("location", {}).get("longitude"),
                "reading_value": entry.get("value"),
                "timestamp": timestamp,
                "record_type": record_type,
            })

    return pd.DataFrame(records)


def transform_historical_weather(historical_list):
    """Transforms a list of historical daily weather responses into a single DataFrame."""
    all_dfs = []
    for item in historical_list:
        daily_json = item.get("data")
        df_day = transform_weather_data(daily_json, record_type="historical")
        if not df_day.empty:
            all_dfs.append(df_day)

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()


# For testing purposes
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Go up one level to reach the 'src' folder and insert into path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pylint: disable=import-error, wrong-import-position
    from extractors.weather_extractor import (
        fetch_historical_weather,
        fetch_real_time_weather,
    )

    print("Testing Transform with Real-Time Data...")
    raw_rt = fetch_real_time_weather()
    df_rt = transform_weather_data(raw_rt, record_type="realtime")

    if not df_rt.empty:
        print(
            f"OOO Success! Transformed real-time DataFrame with {len(df_rt)} rows."
        )
        print(df_rt.head(2))
    else:
        print("XXX Transform failed: Real-time DataFrame is empty.")

    print("\nTesting Transform with Historical Data...")
    raw_hist = fetch_historical_weather(days_back=2)
    df_hist = transform_historical_weather(raw_hist)

    if not df_hist.empty:
        print(
            f"OOO Success! Transformed historical DataFrame with {len(df_hist)}"
            " rows."
        )
        print(df_hist.head(2))
    else:
        print("XXX Transform failed: Historical DataFrame is empty.")
