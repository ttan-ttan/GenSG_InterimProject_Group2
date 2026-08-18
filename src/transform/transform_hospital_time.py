"""Transformer for parsing hospital A&E wait time data into dataframe. """

from datetime import datetime
import re


def parse_patient_count(val):
    """Extracts integer count from patient waiting strings (e.g., '14 patient(s)' -> 14)."""
    if not val or val == "N/A":
        return None
    match = re.search(r'\d+', str(val))
    return int(match.group()) if match else None


def parse_doctor_wait_time(val):
    """Converts doctor wait time strings (hours or minutes) into total minutes,
    decimal hours (for the database schema), and a clean readable format ('X hr Y min').
    """
    if not val or val == "N/A":
        return None, None, "N/A"

    text = str(val).lower()
    numbers = re.findall(r'\d+', text)
    if not numbers:
        return None, None, "N/A"

    val_int = int(numbers[0])

    # Handle hours vs minutes conversion
    if "hour" in text or "hr" in text:
        total_minutes = val_int * 60
    else:
        # Assume minutes (e.g., TTSH format)
        total_minutes = val_int

    # Calculate decimal hours for NUMERIC(4, 2) schema column
    wait_time_hrs = round(total_minutes / 60.0, 2)

    # Format cleanly into 'X hr Y min'
    hours = total_minutes // 60
    mins = total_minutes % 60
    formatted_str = f"{hours} hr {mins} min"

    return total_minutes, wait_time_hrs, formatted_str


def transform_single_hospital_record(record):
    """Cleans and transforms an individual raw hospital dictionary record."""
    if not record:
        return None

    hospital_name = record.get("hospital_name")
    raw_patients = record.get("patients_waiting")
    raw_doctor_wait = record.get("doctor_wait_time")
    updated_at = record.get("updated_at", datetime.now())

    # Standardize values
    patients_count = parse_patient_count(raw_patients)
    total_mins, wait_hrs, formatted_wait = parse_doctor_wait_time(
        raw_doctor_wait)

    # critical info validation: if missing drop the record
    if not hospital_name or wait_hrs is None:
        return None

    # Return structured, analysis-ready record
    transformed_record = {
        "hospital_name": hospital_name,
        "patients_waiting_count": patients_count,
        "doctor_wait_minutes": total_mins,
        "wait_time_hrs": wait_hrs,          # Matches database schema column
        # Clean display format ('X hr Y min')
        "formatted_wait_time": formatted_wait,
        "updated_at": updated_at,
    }

    return transformed_record


def transform_hospital_data(raw_data_list):
    """Iterates through a list of raw hospital records and transforms them."""
    if not raw_data_list:
        return []

    transformed_records = []
    for record in raw_data_list:
        cleaned_record = transform_single_hospital_record(record)
        if cleaned_record:
            transformed_records.append(cleaned_record)

    return transformed_records


# for testing purposes
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Go up one level to reach the 'src' folder and insert into path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    # pylint: disable=import-error, wrong-import-position
    from extractors.hospital_waiting_time_scraper import fetch_all_hospital_data

    # Fetch and transform all records
    raw_results = fetch_all_hospital_data()
    results = transform_hospital_data(raw_results)

    print("\n--- Transformed Hospital Records ---")
    for r in results:
        print(r)
