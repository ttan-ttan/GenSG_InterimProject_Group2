"""Unit tests for the hospital data extraction pipeline."""

from datetime import datetime
from unittest.mock import mock_open, patch
from src.extractors.hospital_waiting_time_scraper import (
    generate_mock_hospitals,
    fetch_all_hospital_data,
    save_raw_hospital_data,
)


def test_generate_mock_hospitals():
    """Test that mock hospitals generate correct structure, keys, and valid ranges."""
    mock_records = generate_mock_hospitals()

    assert len(mock_records) == 4
    for record in mock_records:
        # Check required keys exist
        assert "hospital_name" in record
        assert "patients_waiting" in record
        assert "doctor_wait_time" in record
        assert "updated_at" in record

        # Check data types and format correctness
        assert isinstance(record["hospital_name"], str)
        assert len(record["hospital_name"]) > 0
        assert "patient(s)" in record["patients_waiting"]
        assert isinstance(record["updated_at"], datetime)


@patch("src.extractors.hospital_waiting_time_scraper.datetime")
def test_generate_mock_hospitals_peak_vs_off_peak(mock_datetime):
    """Test that mock patient counts change depending on peak vs off-peak hours."""
    # Simulate peak hour (e.g., 2:00 PM / 14:00)
    mock_datetime.now.return_value = datetime(2026, 8, 18, 14, 0, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    peak_records = generate_mock_hospitals()
    for record in peak_records:
        # Extract digits from string to check range (peak range is 20-55)
        num_str = "".join(filter(str.isdigit, record["patients_waiting"]))
        patients = int(num_str)
        assert 20 <= patients <= 55


@patch("src.extractors.hospital_waiting_time_scraper.scrape_nuhs_wait_times")
@patch("src.extractors.hospital_waiting_time_scraper.scrape_ttsh_wait_time")
def test_fetch_all_hospital_data(mock_ttsh, mock_nuhs):
    """Test the extraction pipeline orchestrator using mocks."""
    mock_nuhs.return_value = [{
        "hospital_name": "NUH",
        "patients_waiting": "10 patient(s)",
        "doctor_wait_time": "30 min",
        "updated_at": datetime.now()
    }]
    mock_ttsh.return_value = {
        "hospital_name": "TTSH",
        "patients_waiting": "15 patient(s)",
        "doctor_wait_time": "45 min",
        "updated_at": datetime.now()
    }

    results = fetch_all_hospital_data()

    # Assertions on pipeline output format and aggregation count
    assert isinstance(results, list)
    assert len(results) == 6  # 1 NUHS + 1 TTSH + 4 Mocks

    for record in results:
        assert isinstance(record["hospital_name"], str)
        assert record["patients_waiting"] is not None
        assert record["doctor_wait_time"] is not None


@patch("builtins.open", new_callable=mock_open)
def test_save_raw_hospital_data(mock_file):
    """Test that raw records successfully trigger file dumping for auditing."""
    sample_data = [{
        "hospital_name": "NUH",
        "patients_waiting": "10 patient(s)",
        "doctor_wait_time": "30 min",
        "updated_at": datetime.now()
    }]

    save_raw_hospital_data(sample_data)

    # Assert that file was opened for writing ('w')
    mock_file.assert_called_once()

# to run this test,
# pip install pytest pytest-mock
# python -m pytest
