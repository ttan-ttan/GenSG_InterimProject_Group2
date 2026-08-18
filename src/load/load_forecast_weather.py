"""Loader module for inserting 2-hour weather forecast records into PostgreSQL."""

from datetime import datetime
from pathlib import Path
import sys

import psycopg2
from psycopg2.extras import execute_values

# Go up two levels to reach root, then point to src folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def load_forecast_to_db(transformed_records, conn, table_name: str = "weather_forecast"):
    """Inserts transformed forecast records into the specified PostgreSQL table."""
    if not transformed_records:
        print("XXX Warning: No forecast records provided for loading.")
        return 0

    records_to_insert = []
    for record in transformed_records:
        records_to_insert.append((
            record.get("area_name"),
            record.get("forecast_text"),
            record.get("will_rain", False),
            record.get("updated_at", datetime.now()),
        ))

    # Using ON CONFLICT (area_name) assuming area_name has a UNIQUE constraint,
    # or simple insert depending on your table design.
    insert_query = f"""
        INSERT INTO {table_name} (area_name, forecast_text, will_rain, updated_at)
        VALUES %s
        ON CONFLICT (area_name) 
        DO UPDATE SET 
            forecast_text = EXCLUDED.forecast_text,
            will_rain = EXCLUDED.will_rain,
            updated_at = EXCLUDED.updated_at;
    """

    success_count = 0
    try:
        with conn.cursor() as cursor:
            execute_values(cursor, insert_query, records_to_insert)
            conn.commit()
        success_count = len(records_to_insert)
        print(
            f"Successfully loaded {success_count} forecast records into '{table_name}'.")
    except psycopg2.Error as e:
        conn.rollback()
        # pylint: disable=broad-exception-caught
        print(f"XXX Error loading forecast data into database: {e}")

    return success_count


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # pylint: disable=import-error, wrong-import-position, no-name-in-module
    from src.extractors.weather_extractor_forecast import fetch_two_hour_forecast
    from src.transform.transform_forecast_weather import transform_two_hour_forecast

    load_dotenv()

    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

        print("Running full 2-Hour Forecast Pipeline...")
        raw_forecast = fetch_two_hour_forecast()
        cleaned_forecast = transform_two_hour_forecast(raw_forecast)

        if cleaned_forecast:
            load_forecast_to_db(cleaned_forecast, connection,
                                table_name="weather_forecast")
        else:
            print("XXX Load test failed: Forecast data is empty.")

        connection.close()
    except psycopg2.Error as db_err:
        print(f"XXX Database connection failed: {db_err}")
