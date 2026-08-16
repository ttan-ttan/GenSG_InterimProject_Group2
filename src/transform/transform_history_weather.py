"""Transformer module for historical weather records and catalyst analysis."""

from datetime import datetime
import pandas as pd


def analyze_breeding_catalysts(df: pd.DataFrame) -> pd.DataFrame:
    """Analyzes 30-45+ day historical weather data to identify mosquito breeding catalysts:
    - Catalyst days: Total daily rainfall between 2.0 mm and 10.0 mm.
    - Tracks consecutive rain and dry streaks.
    """
    if df.empty:
        return df

    # Ensure sorted by date ascending
    df = df.sort_values("record_date").reset_index(drop=True)

    # 1. Identify catalyst days (2.0 mm to 10.0 mm)
    df['is_catalyst_day'] = df['total_rainfall_mm'].between(
        2.0, 10.0, inclusive='both')

    # 2. Identify dry days (0.0 mm rain)
    df['is_dry_day'] = df['total_rainfall_mm'] == 0.0

    # 3. Track rolling streaks (e.g., 3-day rain streaks followed by dry periods)
    df['rain_streak_3days'] = df['is_catalyst_day'].rolling(
        window=3).sum() == 3
    df['dry_streak_3days'] = df['is_dry_day'].rolling(window=3).sum() == 3

    return df


def transform_historical_weather_data(raw_records):
    """Processes raw historical records into a clean format ready for database insertion."""
    if not raw_records:
        print("XXX Warning: Raw historical weather data is empty.")
        return []

    # Convert to DataFrame to utilize analysis logic
    df = pd.DataFrame(raw_records)

    # Ensure proper data types
    df['record_date'] = pd.to_datetime(df['record_date']).dt.date
    df['total_rainfall_mm'] = pd.to_numeric(
        df['total_rainfall_mm'], errors='coerce').fillna(0.0)

    # Apply breeding catalyst analysis logic
    df = analyze_breeding_catalysts(df)

    transformed_records = []
    for _, row in df.iterrows():
        transformed_records.append({
            "record_date": row["record_date"],
            "total_rainfall_mm": float(row["total_rainfall_mm"]),
            "is_catalyst_day": bool(row["is_catalyst_day"])
        })

    print(
        f"Successfully transformed {len(transformed_records)} historical weather records.")
    return transformed_records
