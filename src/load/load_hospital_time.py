"""Loader module for inserting cleaned hospital A&E wait time records into PostgreSQL database tables."""

from datetime import datetime
from pathlib import Path
import sys
import pandas as pd

import psycopg2
from psycopg2.extras import execute_values

# Go up two levels from src/loaders/ to reach root, then point to src folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def load_hospital_data_to_db(transformed_records, conn, table_name: str = "hospital_wait_times"):
    """Inserts transformed hospital wait time records into the specified PostgreSQL table."""
    if not transformed_records:
        print("XXX Warning: No hospital records provided for loading.")
        return 0

    # Map records to match the updated table schema columns:
    # hospital_name, patients_waiting_count, doctor_wait_minutes, wait_time_hrs, updated_at
    records_to_insert = []
    for record in transformed_records:
        records_to_insert.append((
            record.get("hospital_name"),
            record.get("patients_waiting_count"),
            record.get("doctor_wait_minutes"),
            record.get("wait_time_hrs"),
            record.get("updated_at", datetime.now()),
        ))

    insert_query = f"""
        INSERT INTO {table_name} (hospital_name, patients_waiting_count, doctor_wait_minutes, wait_time_hrs, updated_at)
        VALUES %s
    """

    success_count = 0
    try:
        with conn.cursor() as cursor:
            execute_values(cursor, insert_query, records_to_insert)
            conn.commit()
        success_count = len(records_to_insert)
        print(
            f"Successfully loaded {success_count} hospital records into '{table_name}'.")
    except psycopg2.Error as e:
        conn.rollback()
        # pylint: disable=broad-exception-caught
        print(f"XXX Error loading hospital data into database: {e}")

    return success_count


# for testing purposes
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # pylint: disable=import-error, wrong-import-position, no-name-in-module
    from src.extractors.hospital_waiting_time_scraper import fetch_all_hospital_data
    from src.transform.transform_hospital_time import transform_hospital_data

    load_dotenv()

    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

        print("Running full Hospital Pipeline (ETL -> PostgreSQL)...")
        raw_data = fetch_all_hospital_data()
        cleaned_data = transform_hospital_data(raw_data)

        if cleaned_data:
            load_hospital_data_to_db(
                cleaned_data, connection, table_name="hospital_wait_times")
            df = pd.DataFrame(cleaned_data)
            output_path = Path(__file__).resolve(
            ).parent.parent.parent / "data" / "processed" / "hospital_wait_times.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(
                f"Successfully saved processed hospital CSV to {output_path}")
        else:
            print("XXX Load test failed: Transformed hospital data is empty.")

        connection.close()
    except psycopg2.Error as db_err:
        print(f"XXX Database connection failed: {db_err}")
