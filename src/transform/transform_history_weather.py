"""Transformer for historical weather records with area names and catalyst analysis."""

import pandas as pd

# set breeding catalyst condition to rainfall 2mm-10mm daily +3day rain 3 day stop


def get_postal_prefix_from_area(area_name: str) -> str:
    """Maps weather station area names to their corresponding Singapore postal prefix/district."""
    if not area_name:
        return "Unknown"

    # Mapping dictionary based on your routing/region logic
    mapping = {
        "Ang Mo Kio": "D20",
        "Bishan": "D20",
        "Clementi": "D05",
        "West Coast": "D05",
        "Bedok": "D16",
        "Changi": "D17",
        "Jurong": "D22",
        "Yishun": "D27",
        "Woodlands": "D25"
    }

    for key, prefix in mapping.items():
        if key.lower() in area_name.lower():
            return prefix

    return "D01"  # Default fallback district code


def analyze_breeding_catalysts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df['breeding_catalyst_valid'] = False
        return df

    df = df.sort_values(["area_name", "record_date"]).reset_index(drop=True)

    is_catalyst_day = df['total_rainfall_mm'].between(
        2.0, 10.0, inclusive='both')
    is_dry_day = df['total_rainfall_mm'] == 0.0

    rain_streak_3days = (
        df.groupby('area_name', group_keys=False)
        .apply(lambda x: is_catalyst_day.loc[x.index].rolling(window=3, min_periods=3).sum() == 3)
    )

    dry_streak_3days = (
        df.groupby('area_name', group_keys=False)
        .apply(lambda x: is_dry_day.loc[x.index].rolling(window=3, min_periods=3).sum() == 3)
    )

    df['breeding_catalyst_valid'] = rain_streak_3days.shift(
        3) & dry_streak_3days

    return df


def transform_historical_weather_data(raw_records):
    if not raw_records:
        print("XXX Warning: Raw historical weather data is empty.")
        return []

    df = pd.DataFrame(raw_records)

    df['record_date'] = pd.to_datetime(df['record_date']).dt.date
    df['total_rainfall_mm'] = pd.to_numeric(
        df['total_rainfall_mm'], errors='coerce').fillna(0.0)

    # Generate postal prefix dynamically based on area name
    df['postal_prefix'] = df['area_name'].apply(get_postal_prefix_from_area)

    df = analyze_breeding_catalysts(df)

    transformed_records = []
    for _, row in df.iterrows():
        transformed_records.append({
            "area_name": str(row["area_name"]),
            "postal_prefix": str(row["postal_prefix"]),
            "record_date": row["record_date"],
            "total_rainfall_mm": float(row["total_rainfall_mm"]),
            "is_catalyst_day": bool(row["breeding_catalyst_valid"])
        })

    print(
        f"OOO Successfully transformed {len(transformed_records)} historical weather records.")
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
