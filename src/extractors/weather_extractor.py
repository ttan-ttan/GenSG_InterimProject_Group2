"""Extractor module for real-time rainfall data from data.gov.sg."""

import requests


def fetch_real_time_rainfall(date_str: str = None) -> dict:
    """
    Fetches real-time or specific date/time rainfall readings across Singapore.
    :param date_str: Optional string in 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS' format.
    :return: Dictionary containing stations and readings, or empty dict on failure.
    """
    url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    params = {}

    if date_str:
        params["date"] = date_str

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            result = response.json()
            # The API returns code 0 or 1 depending on success structure;
            # checking data presence is safest.
            if "data" in result and result["data"]:
                print("[Rainfall API]: Successfully retrieved readings.")
                return result["data"]

        print(
            f"[Rainfall API Warning]: Failed with status code {response.status_code}")
        return {}

    except requests.exceptions.RequestException as e:
        print(f"[Rainfall API Error]: Connection error occurred ({e}).")
        return {}
