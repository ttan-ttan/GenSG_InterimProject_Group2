"""Transformer for historical weather records with area names and catalyst analysis."""

import pandas as pd

# set breeding catalyst condition to rainfall 2mm-10mm daily +3day rain 3 day stop


def analyze_breeding_catalysts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df['breeding_catalyst_valid'] = False
        return df

    # 1. Ensure sorted by area and date asc
    df = df.sort_values(["area_name", "record_date"]).reset_index(drop=True)

    # 2. Individual day conditions
    is_catalyst_day = df['total_rainfall_mm'].between(
        2.0, 10.0, inclusive='both')
    is_dry_day = df['total_rainfall_mm'] == 0.0

    # 3. Rolling 3-day streaks grouped by area_name
    rain_streak_3days = (
        df.groupby('area_name', group_keys=False)
        .apply(lambda x: is_catalyst_day.loc[x.index].rolling(window=3, min_periods=3).sum() == 3)
    )

    dry_streak_3days = (
        df.groupby('area_name', group_keys=False)
        .apply(lambda x: is_dry_day.loc[x.index].rolling(window=3, min_periods=3).sum() == 3)
    )

    # 4. Combine
    df['breeding_catalyst_valid'] = rain_streak_3days.shift(
        3) & dry_streak_3days

    return df

# main transform function to clean based on data schema. rainfall NA --> 0


def transform_historical_weather_data(raw_records):
    if not raw_records:
        print("XXX Warning: Raw historical weather data is empty.")
        return []

    # Convert to DataFrame to utilize analysis logic
    df = pd.DataFrame(raw_records)

    # Ensure proper data types
    df['record_date'] = pd.to_datetime(df['record_date']).dt.date
    df['total_rainfall_mm'] = pd.to_numeric(
        df['total_rainfall_mm'], errors='coerce').fillna(0.0)

    # Apply breeding catalyst analysis logic group-wise per area
    df = analyze_breeding_catalysts(df)

    transformed_records = []
    for _, row in df.iterrows():
        transformed_records.append({
            "area_name": str(row["area_name"]),
            "record_date": row["record_date"],
            "total_rainfall_mm": float(row["total_rainfall_mm"]),
            "breeding_catalyst_valid": bool(row["breeding_catalyst_valid"])
        })

    print(
        f"OOO Successfully transformed {len(transformed_records)} historical weather records with area names.")
    return transformed_records


if __name__ == "__main__":
    print("Testing Transformer with simulated extracted historical output...")

    # Simulating data structure returned by your extractor module
    extracted_mock_data = [
        {"area_name": "Ang Mo Kio", "record_date": "2026-06-01",
            "total_rainfall_mm": 5.5},
        {"area_name": "Ang Mo Kio", "record_date": "2026-06-02",
            "total_rainfall_mm": 3.0},
        {"area_name": "Ang Mo Kio", "record_date": "2026-06-03",
            "total_rainfall_mm": 8.1},
        {"area_name": "Clementi", "record_date": "2026-06-01", "total_rainfall_mm": 0.0},
        {"area_name": "Clementi", "record_date": "2026-06-02", "total_rainfall_mm": 0.0}
    ]

    transformed = transform_historical_weather_data(extracted_mock_data)
    print("Transformed Output Sample:")
    print(transformed[:3])
