"""Module for fetching database records and forecasting hospital wait times."""

import os
from datetime import datetime
import psycopg2
from psycopg2 import OperationalError, Error
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


def forecast_hospital_wait_time(hospital_name, base_minutes):
    """
    Forecasts wait times for hospitals by applying environmental penalties 
    (weather, time of day) onto a historical or static baseline.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
    except (OperationalError, Error) as e:
        print(
            f"[DB Warning]: Could not connect to database for prediction ({e}). Using base values.")
        return round(base_minutes, 2)

    current_multiplier = 1.0

    try:
        # Check current weather conditions from your weather_records table
        cur.execute("""
            SELECT is_heavy_rain 
            FROM weather_records 
            ORDER BY recorded_at DESC 
            LIMIT 1;
        """)
        weather_row = cur.fetchone()

        if weather_row and weather_row[0]:
            current_multiplier += 0.30  # +30% penalty for rain/accidents
            print(
                f"[{hospital_name}] Heavy rain detected in DB: applying +30% weather penalty.")

        # Check peak hour constraints (e.g., 6 PM - 10 PM)
        current_hour = datetime.now().hour
        if 18 <= current_hour <= 22:
            current_multiplier += 0.20  # +20% penalty for evening peak hours
            print(
                f"[{hospital_name}] Peak hour detected: applying +20% time penalty.")

    except (OperationalError, Error) as e:
        print(
            f"Database query error during environmental check for {hospital_name}: {e}")
    finally:
        cur.close()
        conn.close()

    final_estimated_wait = round(base_minutes * current_multiplier, 2)
    return final_estimated_wait
