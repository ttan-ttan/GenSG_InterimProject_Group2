"""Unit tests for the hospital database loader module."""

from datetime import datetime
from unittest.mock import MagicMock, patch
import psycopg2
from src.load.load_hospital_time import load_hospital_data_to_db


@patch("src.load.load_hospital_time.execute_values")
def test_load_hospital_data_to_db_success(mock_execute_values):
    """Test successful bulk database insertion using mocks."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    sample_data = [{
        "hospital_name": "NUH",
        "patients_waiting_count": 20,
        "doctor_wait_minutes": 60,
        "wait_time_hrs": 1.0,
        "updated_at": datetime.now()
    }]

    inserted_count = load_hospital_data_to_db(
        sample_data, mock_conn, table_name="test_table")

    assert inserted_count == 1
    mock_execute_values.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


@patch("src.load.load_hospital_time.execute_values")
def test_load_hospital_data_db_exception_rollback(mock_execute_values):
    """Test that a database error triggers a transaction rollback and re-raises the exception."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Simulate a database failure (e.g., connection drop or query constraint error) during execute_values
    mock_execute_values.side_effect = psycopg2.DatabaseError("Connection lost")

    sample_data = [{
        "hospital_name": "NUH",
        "patients_waiting_count": 20,
        "doctor_wait_minutes": 60,
        "wait_time_hrs": 1.0,
        "updated_at": datetime.now()
    }]

    try:
        load_hospital_data_to_db(
            sample_data, mock_conn, table_name="test_table")
    except psycopg2.DatabaseError:
        pass

    # Verify rollback was called and commit was avoided
    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()


def test_load_hospital_data_empty_list():
    """Test behavior when passed an empty list of records."""
    mock_conn = MagicMock()
    count = load_hospital_data_to_db([], mock_conn)
    assert count == 0
    mock_conn.cursor.assert_not_called()
