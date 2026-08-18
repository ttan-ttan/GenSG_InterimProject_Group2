"""Unit tests for the hospital data transformation module."""

from datetime import datetime
from src.transform.transform_hospital_time import (
    parse_patient_count,
    parse_doctor_wait_time,
    transform_single_hospital_record,
    transform_hospital_data,
)


def test_parse_patient_count():
    """Test extracting valid integer counts from raw strings."""
    assert parse_patient_count("42 patient(s)") == 42
    assert parse_patient_count("5") == 5
    assert parse_patient_count("N/A") is None
    assert parse_patient_count(None) is None


def test_parse_doctor_wait_time_minutes():
    """Test parsing standard minute-based wait times."""
    total_mins, wait_hrs, formatted = parse_doctor_wait_time("90 min")
    assert total_mins == 90
    assert wait_hrs == 1.5
    assert formatted == "1 hr 30 min"


def test_parse_doctor_wait_time_hours():
    """Test parsing hour-based wait times."""
    total_mins, wait_hrs, formatted = parse_doctor_wait_time("2 hours")
    assert total_mins == 120
    assert wait_hrs == 2.0
    assert formatted == "2 hr 0 min"


def test_parse_doctor_wait_time_invalid():
    """Test handling of missing or unparseable wait time strings."""
    total_mins, wait_hrs, formatted = parse_doctor_wait_time("N/A")
    assert total_mins is None
    assert wait_hrs is None
    assert formatted == "N/A"


def test_transform_single_hospital_record_success():
    """Test successful transformation and whitespace stripping for a single record."""
    raw_input = {
        "hospital_name": " National University Hospital ",
        "patients_waiting": "42 patient(s)",
        "doctor_wait_time": "90 min",
        "updated_at": datetime(2026, 8, 18, 12, 0, 0),
    }

    result = transform_single_hospital_record(raw_input)

    assert result is not None
    # Verify whitespace stripping rule
    assert result["hospital_name"] == "National University Hospital"
    assert result["patients_waiting_count"] == 42
    assert result["doctor_wait_minutes"] == 90
    assert result["wait_time_hrs"] == 1.5
    assert result["formatted_wait_time"] == "1 hr 30 min"


def test_transform_single_hospital_record_missing_critical_data():
    """Test that records with missing critical data (like wait times) are dropped (returns None)."""
    raw_input = {
        "hospital_name": "TTSH",
        "patients_waiting": "10 patient(s)",
        "doctor_wait_time": "N/A",  # Missing critical doctor wait time
    }

    result = transform_single_hospital_record(raw_input)
    assert result is None


def test_transform_hospital_data_list_success():
    """Test batch transformation of a list containing multiple records."""
    raw_list = [
        {
            "hospital_name": "NUH",
            "patients_waiting": "20 patient(s)",
            "doctor_wait_time": "60 min",
        },
        {
            "hospital_name": "Invalid Hospital",
            "patients_waiting": "5 patient(s)",
            "doctor_wait_time": "N/A",  # Should be dropped
        },
    ]

    results = transform_hospital_data(raw_list)

    # Only 1 record should pass the filter criteria
    assert len(results) == 1
    assert results[0]["hospital_name"] == "NUH"
    assert results[0]["doctor_wait_minutes"] == 60


def test_transform_hospital_data_empty_input():
    """Test batch transformation handles empty lists or None gracefully."""
    assert transform_hospital_data([]) == []
    assert transform_hospital_data(None) == []
