"""Loader module for inserting historical weather records into PostgreSQL."""

from pathlib import Path
import sys

import psycopg2
from psycopg2.extras import execute_values

# Go up two levels to reach root, then point to src folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def load_historical_weather_to_db(transformed_records, conn, table_name: str = "weather_history"):
    """Inserts transformed historical weather records into the specified PostgreSQL table."""
    if not transformed_records:
        print("XXX Warning: No historical weather records provided for loading.")
        return 0

    records_to_insert = []
    for record in transformed_records:
        records_to_insert.append((
            record.get("area_name"),
            record.get("record_date"),
            record.get("total_rainfall_mm"),
            record.get("is_catalyst_day", False),
        ))

    # Using ON CONFLICT with composite key (area_name, record_date) to update if record already exists
    insert_query = f"""
        INSERT INTO {table_name} (area_name, record_date, total_rainfall_mm, is_catalyst_day)
        VALUES %s
        ON CONFLICT (area_name, record_date) 
        DO UPDATE SET 
            total_rainfall_mm = EXCLUDED.total_rainfall_mm,
            is_catalyst_day = EXCLUDED.is_catalyst_day;
    """

    success_count = 0
    try:
        with conn.cursor() as cursor:
            execute_values(cursor, insert_query, records_to_insert)
            conn.commit()
        success_count = len(records_to_insert)
        print(
            f"Successfully loaded {success_count} historical weather records into '{table_name}'.")
    except psycopg2.Error as e:
        conn.rollback()
        # pylint: disable=broad-exception-caught
        print(f"XXX Error loading historical weather data into database: {e}")

    return success_count


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # pylint: disable=import-error, wrong-import-position, no-name-in-module
    from src.extractors.weather_extractor_history import fetch_historical_weather_data
    from src.transform.transform_history_weather import transform_historical_weather_data

    load_dotenv()

    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

        print("Running full Historical Weather Pipeline...")
        raw_history = fetch_historical_weather_data(60)
        cleaned_history = transform_historical_weather_data(raw_history)

        if cleaned_history:
            load_historical_weather_to_db(
                cleaned_history, connection, table_name="weather_history")
        else:
            print("XXX Load test failed: Historical data is empty.")

        connection.close()
    except psycopg2.Error as db_err:
        print(f"XXX Database connection failed: {db_err}")
