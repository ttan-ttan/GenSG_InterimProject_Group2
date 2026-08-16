"""Load module for inserting transformed weather DataFrames into PostgreSQL database tables."""

from pathlib import Path
import sys

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Go up one level to reach the 'src' folder to import transform_data module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_weather_data(df: pd.DataFrame, conn, table_name: str = "weather_records"):
    """Loads a transformed weather DataFrame into the specified PostgreSQL table."""
    if df.empty:
        print("XXX Warning: DataFrame is empty. No data to load.")
        return

    # Map DataFrame columns to match table schema:
    # table columns: area_name, forecast, is_heavy_rain, recorded_at
    records_to_insert = []
    for _, row in df.iterrows():
        records_to_insert.append((
            row.get("station_name", "Unknown Area"),  # maps to area_name
            # maps to forecast (if applicable)
            row.get("forecast", "N/A"),
            False,                                     # is_heavy_rain default/derived logic
            row.get("timestamp"),                      # maps to recorded_at
        ))

    insert_query = f"""
        INSERT INTO {table_name} (area_name, forecast, is_heavy_rain, recorded_at)
        VALUES %s
    """

    try:
        with conn.cursor() as cursor:
            execute_values(cursor, insert_query, records_to_insert)
            conn.commit()
        print(
            f"Successfully loaded {len(records_to_insert)} rows into '{table_name}'.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"XXX Error loading data into database: {e}")


# For testing purposes
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # pylint: disable=import-error, wrong-import-position
    from transform.transform_weather import transform_weather_data
    from extractors.weather_extractor import fetch_real_time_weather

    load_dotenv()

    # Test database connection setup
    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

        print("Testing Pipeline Load Step...")
        raw_data = fetch_real_time_weather()
        transformed_df = transform_weather_data(raw_data)

        if not transformed_df.empty:
            load_weather_data(transformed_df, connection,
                              table_name="weather_records")
        else:
            print("XXX Load test failed: Transformed data is empty.")

        connection.close()
    except psycopg2.Error as db_err:
        print(f"XXX Database connection failed: {db_err}")
