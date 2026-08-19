"""Loader module for inserting cleaned weather records into PostgreSQL database tables."""

from datetime import datetime
from pathlib import Path
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Go up two levels from src/load/ to reach root, then point to src folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def load_weather_data_to_db(transformed_records, conn, table_name: str = "weather_realtime"):
    """Inserts transformed weather records into the specified PostgreSQL table."""
    if not transformed_records:
        print("XXX Warning: No weather records provided for loading.")
        return 0

    records_to_insert = []
    for record in transformed_records:
        records_to_insert.append((
            record.get("area_name"),
            record.get("postal_prefix"),
            record.get("reading_value", 0.0),
            record.get("is_heavy_rain", False),
            record.get("recorded_at", datetime.now()),
        ))

    insert_query = f"""
        INSERT INTO {table_name} (area_name, postal_prefix, reading_value, is_heavy_rain, recorded_at)
        VALUES %s
        ON CONFLICT (area_name, recorded_at) 
        DO UPDATE SET 
            postal_prefix = EXCLUDED.postal_prefix,
            reading_value = EXCLUDED.reading_value,
            is_heavy_rain = EXCLUDED.is_heavy_rain;
    """

    success_count = 0
    try:
        with conn.cursor() as cursor:
            execute_values(cursor, insert_query, records_to_insert)
            conn.commit()
        success_count = len(records_to_insert)
        print(
            f"Successfully loaded {success_count} weather records into '{table_name}'.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"XXX Error loading weather data into database: {e}")

    return success_count


# Main execution block for testing the weather loader pipeline standalone
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # pylint: disable=import-error, wrong-import-position, no-name-in-module
    from src.extractors.weather_extractor_realtime import fetch_real_time_weather
    from src.transform.transform_realtime_weather import transform_real_time_weather

    load_dotenv()

    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

        print("Running full Weather Pipeline (ETL -> PostgreSQL)...")
        raw_weather_data = fetch_real_time_weather()
        cleaned_weather_data = transform_real_time_weather(raw_weather_data)

        if cleaned_weather_data:
            load_weather_data_to_db(
                cleaned_weather_data, connection, table_name="weather_realtime"
            )

            # Export processed CSV for visualization
            df = pd.DataFrame(cleaned_weather_data)
            transformed_file = (
                Path(__file__).resolve().parent.parent.parent
                / "data"
                / "processed"
                / "weather_now.csv"
            )
            transformed_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(transformed_file, index=False)
            print(
                f"Successfully saved processed weather CSV to {transformed_file}")
        else:
            print("XXX Load test failed: Transformed weather data is empty.")

        connection.close()
    except psycopg2.Error as db_err:
        print(f"XXX Database connection failed: {db_err}")
