"""Transformer module for historical weather records with area names and catalyst analysis."""

from datetime import datetime
import pandas as pd


def analyze_breeding_catalysts(df: pd.DataFrame) -> pd.DataFrame:
    """Analyzes historical weather data per area to identify mosquito breeding catalysts:
    - Catalyst days: Total daily rainfall between 2.0 mm and 10.0 mm.
    - Tracks consecutive rain and dry streaks per area.
    """
    if df.empty:
        return df

    # Ensure sorted by area and date ascending so rolling operations work correctly per station/area
    df = df.sort_values(["area_name", "record_date"]).reset_index(drop=True)

    # 1. Identify catalyst days (2.0 mm to 10.0 mm)
    df['is_catalyst_day'] = df['total_rainfall_mm'].between(
        2.0, 10.0, inclusive='both')

    # 2. Identify dry days (0.0 mm rain)
    df['is_dry_day'] = df['total_rainfall_mm'] == 0.0

    # 3. Track rolling streaks grouped by area_name to prevent cross-area pollution
    df['rain_streak_3days'] = (
        df.groupby('area_name')['is_catalyst_day']
        .rolling(window=3, min_periods=3)
        .sum()
        .reset_index(level=0, drop=True) == 3
    )

    df['dry_streak_3days'] = (
        df.groupby('area_name')['is_dry_day']
        .rolling(window=3, min_periods=3)
        .sum()
        .reset_index(level=0, drop=True) == 3
    )

    return df


def transform_historical_weather_data(raw_records):
    """Processes raw historical records (including area names) into a clean format ready for database insertion."""
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
            "is_catalyst_day": bool(row["is_catalyst_day"])
        })

    print(
        f"Successfully transformed {len(transformed_records)} historical weather records with area names.")
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
