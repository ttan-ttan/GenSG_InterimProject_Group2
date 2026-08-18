"""Transform pipeline for Singapore Dengue Cluster data.

Automatically checks for the geocoded source file and runs geocode.py if missing,
then cleans fields, standardizes data types, and saves the analytics-ready dataset.
"""

import os
import subprocess
import sys
from pathlib import Path
import pandas as pd

# Go up two levels to reach root, then point to src folder for module compatibility
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def ensure_geocoded_data_exists() -> str:
    """Checks if the source CSV from geocode.py exists. If not, runs geocode.py automatically."""
    input_file = Path(__file__).resolve().parent.parent.parent / \
        "data" / "processed" / "dengue_cluster_postal_codes.csv"

    if os.path.exists(input_file):
        print(f"OOO Found existing geocoded data at {input_file}")
        return str(input_file)

    print(f"--- {input_file} not found. Automatically triggering geocode.py...")

    # Point directly to src/extractors/geocode.py relative to the project root
    geocode_script = Path(__file__).resolve(
    ).parent.parent.parent / "src" / "extractors" / "geocode.py"

    if not os.path.exists(geocode_script):
        raise FileNotFoundError(
            f"Could not locate geocode.py at {geocode_script}. Please check your workspace path."
        )

    # Run geocode.py as a subprocess to generate the required file
    result = subprocess.run(
        ["python", str(geocode_script)], capture_output=False)
    if result.returncode != 0:
        raise RuntimeError(
            "Automatic execution of geocode.py failed. Please check your OneMap token and network connection.")

    if not os.path.exists(input_file):
        raise FileNotFoundError(
            f"Geocoding finished, but expected output file {input_file} was still not found.")

    return str(input_file)


def transform_dengue_data(input_path: str) -> pd.DataFrame:
    """Transforms the geocoded dengue CSV data into a clean, analytics-ready dataset."""
    print(f"Loading processed data from {input_path}...")
    df = pd.read_csv(input_path)

    # 1. Handle missing values
    df["POSTAL"] = df["POSTAL"].fillna("").astype(str).str.zfill(6)
    df["POSTAL_PREFIX"] = df["POSTAL_PREFIX"].fillna("").astype(str)
    df["BLK_NO"] = df["BLK_NO"].fillna("")
    df["ROAD_NAME"] = df["ROAD_NAME"].fillna("")
    df["BUILDING"] = df["BUILDING"].fillna("")
    df["ADDRESS"] = df["ADDRESS"].fillna("")

    # 2. Ensure numeric types are properly cast
    df["CASE_SIZE"] = pd.to_numeric(
        df["CASE_SIZE"], errors="coerce").fillna(0).astype(int)
    df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
    df["MATCH_COUNT"] = pd.to_numeric(
        df["MATCH_COUNT"], errors="coerce").fillna(0).astype(int)

    # 3. Drop exact duplicate rows if any exist
    initial_count = len(df)
    df = df.drop_duplicates()
    print(
        f"Dropped {initial_count - len(df)} duplicate rows during transformation.")

    print(
        f"Transformation complete. Cleaned dataset contains {len(df)} records.")
    return df


if __name__ == "__main__":
    print("Running Dengue Transform Pipeline...")

    try:
        # Step 1: Ensure raw/geocoded file exists (runs geocode.py automatically if missing)
        input_file = ensure_geocoded_data_exists()

        output_file_path = Path(__file__).resolve(
        ).parent.parent.parent / "data" / "processed" / "dengue_clusters_transformed.csv"

        # Step 2: Transform data
        transformed_df = transform_dengue_data(input_file)

        # Step 3: Save output
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        transformed_df.to_csv(output_file_path, index=False, encoding="utf-8")
        print(f"OOO Saved transformed data to {output_file_path}")

    except Exception as e:
        print(f"XXX Error during transform pipeline execution: {e}")
