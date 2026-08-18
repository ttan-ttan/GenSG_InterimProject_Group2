"""Extractor specifically for real-time Singapore Dengue Cluster GeoJSON data from data.gov.sg."""
import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import json

load_dotenv()

# Configuration from environment variables with safe defaults
DENGUE_DATASET_ID = os.getenv(
    "DENGUE_DATASET_ID", "d_dbfabf16158d1b0e1c420627c0819168")
POLL_DOWNLOAD_URL = f"https://api-open.data.gov.sg/v1/public/api/datasets/{DENGUE_DATASET_ID}/poll-download"


def save_raw_dengue_data(raw_records):
    """Saves the raw dengue cluster GeoJSON data to a JSON file for debugging and record-keeping."""
    output_path = Path(__file__).parent.parent.parent / "data" / \
        "raw" / "raw_dengue_clusters.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_records, f, indent=4, default=str)
        print(
            f"OOO Successfully saved raw dengue cluster data to {output_path}")
    except Exception as e:
        print(f"XXX Error saving raw dengue cluster data: {e}")


def fetch_real_time_dengue():
    """Extracts the latest real-time dengue cluster snapshot via data.gov.sg poll-download API."""
    try:
        headers = {}
        api_key = os.getenv("DATAGOV_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key

        # Step 1: Poll the dataset endpoint to get the active download URL (supporting 200/201 responses)
        poll_response = requests.get(
            POLL_DOWNLOAD_URL, headers=headers, timeout=60)
        if poll_response.status_code not in [200, 201]:
            print(
                f"XXX Error polling dengue dataset catalog: status code {poll_response.status_code}")
            return None

        json_data = poll_response.json()
        if json_data.get('code') != 0:
            print(
                f"XXX Error from API: {json_data.get('errMsg', 'Unknown error')}")
            return None

        download_url = json_data.get('data', {}).get('url')
        if not download_url:
            print("XXX Error: Download URL not found in poll response.")
            return None

        # Step 2: Download the actual GeoJSON file contents from the signed link
        data_response = requests.get(download_url, timeout=120)
        if data_response.status_code == 200:
            return data_response.json()
        else:
            print(
                f"XXX Error downloading dengue GeoJSON data: {data_response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"XXX Network error fetching real-time dengue data: {e}")
        return None


if __name__ == "__main__":
    print("Testing Real-Time Dengue Extractor...")
    data = fetch_real_time_dengue()
    if data:
        features = data.get("features", [])
        print(
            f"OOO Success! Fetched {len(features)} active dengue cluster features.")
        save_raw_dengue_data(data)
    else:
        print("XXX Test failed: No real-time dengue data returned.")
