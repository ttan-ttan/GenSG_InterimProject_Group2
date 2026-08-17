"""Look up Singapore postal codes from free text using the OneMap Search API."""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = "https://www.onemap.gov.sg/api/common/elastic/search"


def get_postal_code(search_val: str) -> Optional[str]:
    """Return the postal code for the best-matching result of a OneMap search.

    search_val can be a building name, road name, bus stop number, or postal code.
    Returns None if no result is found.
    """
    token = os.getenv("ONEMAP_TOKEN")
    if not token:
        raise RuntimeError("ONEMAP_TOKEN is not set in the environment (.env file).")

    response = requests.get(
        SEARCH_URL,
        params={
            "searchVal": search_val,
            "returnGeom": "N",
            "getAddrDetails": "Y",
            "pageNum": 1,
        },
        headers={"Authorization": token},
    )
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        return None
    return results[0]["POSTAL"]


if __name__ == "__main__":
    query = input("Enter a building name, road name, or address: ").strip()
    postal_code = get_postal_code(query)
    if postal_code:
        print(f"Postal code: {postal_code}")
    else:
        print("No results found.")
