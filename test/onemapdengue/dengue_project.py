import os
import requests
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

email = os.getenv("ONEMAP_EMAIL")
password = os.getenv("ONEMAP_PASSWORD")

print(email)

# Get OneMap access token
url = "https://www.onemap.gov.sg/api/auth/post/getToken"

payload = {
    "email": email,
    "password": password
}

response = requests.post(url, json=payload)

response.raise_for_status()

token = response.json()["access_token"]

print("OneMap authentication successful")

# Retrieve dengue clusters
url = "https://www.onemap.gov.sg/api/public/themesvc/retrieveTheme"

headers = {
    "Authorization": token
}

params = {
    "queryName": "dengue_cluster"
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

response.raise_for_status()

dengue_data = response.json()

print("Dengue cluster data retrieved")

print(dengue_data.keys())

clusters = dengue_data["SrchResults"]

print("Number of clusters:", len(clusters))

print(clusters[0])