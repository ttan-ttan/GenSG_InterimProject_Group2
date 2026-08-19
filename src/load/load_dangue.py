"""Load pipeline for Singapore Dengue Cluster data.

Reads the transformed dengue clusters dataset, cleans postal prefixes into standard 
district formats (e.g., D80) while handling NaN/unknown values gracefully, 
and loads the data into the PostgreSQL database.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Go up two levels to reach root, then point to src folder for module compatibility
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def determine_severity(case_size: int) -> str:
    """Determines cluster severity based on case count size."""
    if case_size >= 10:
        return "High"
    elif case_size >= 5:
        return "Medium"
    return "Low"


def clean_postal_district(prefix) -> str:
    """Cleans postal prefix and formats it as D + prefix (e.g., 80 -> D80), handling NaN/nulls safely."""
    if pd.isna(prefix):
        return "Unknown"

    prefix_str = str(prefix).strip()

    # Handle missing, null, or string 'nan' values gracefully to avoid 'Dnan'
    if prefix_str.lower() in ["nan", "none", "", "nat"]:
        return "Unknown"

    # Remove float decimal points if present (e.g., "80.0" -> "80")
    if "." in prefix_str:
        prefix_str = prefix_str.split(".")[0]

    if prefix_str.isdigit():
        return f"D{prefix_str.zfill(2)}"

    return f"D{prefix_str}"


def load_dengue_data_to_db(csv_path: str) -> None:
    """Loads transformed dengue data into the PostgreSQL database matching the specified schema."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Transformed CSV file not found at {csv_path}. Please run transform_dangue.py first.")

    print(f"Loading transformed data from {csv_path}...")
    df = pd.read_csv(csv_path)

    if df.empty:
        print("--- DataFrame is empty. No records to load.")
        return

    records = []
    for _, row in df.iterrows():
        postal_district = clean_postal_district(row.get("POSTAL_PREFIX"))
        location_name = str(row.get("LOCALITY", "")).strip(
        ) if pd.notna(row.get("LOCALITY")) else "Unknown"
        case_count = int(row.get("CASE_SIZE", 0) or 0)
        cluster_severity = determine_severity(case_count)

        report_month = str(row.get("FMEL_UPD_D", "2026-08"))[:7]

        records.append((
            postal_district,
            location_name,
            case_count,
            cluster_severity,
            report_month
        ))

    print(f"Connecting to database {DB_NAME} on {DB_HOST}:{DB_PORT}...")
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        cursor = connection.cursor()

        # Re-create table to ensure clean schema structure matching requirements
        cursor.execute("DROP TABLE IF EXISTS dengue_clusters;")

        cursor.execute("""
            CREATE TABLE dengue_clusters (
                id SERIAL PRIMARY KEY,
                postal_district VARCHAR(20),
                location_name VARCHAR(150),
                case_count INT DEFAULT 0,
                cluster_severity VARCHAR(50),
                report_month VARCHAR(20)
            );
        """)

        insert_query = """
            INSERT INTO dengue_clusters (
                postal_district, location_name, case_count, cluster_severity, report_month
            ) VALUES %s
        """

        df.to_csv('data/processed/dengue_clusters_transformed.csv', index=False)

        print(f"Inserting {len(records)} records into PostgreSQL database...")
        execute_values(cursor, insert_query, records)

        connection.commit()
        print(
            f"OOO Successfully loaded {len(records)} dengue cluster records into the database.")

    except Exception as e:
        print(f"XXX Database load failed: {e}")
        if 'connection' in locals() and connection:
            connection.rollback()
        raise
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


if __name__ == "__main__":
    print("Running Dengue Load Pipeline...")
    transformed_file = Path(__file__).resolve(
    ).parent.parent.parent / "data" / "processed" / "dengue_clusters_transformed.csv"

    try:
        load_dengue_data_to_db(str(transformed_file))
    except Exception as e:
        print(f"XXX Error during load pipeline execution: {e}")
