import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from datetime import timedelta


# ============================================================
# 1. DATABASE CONNECTION
# ============================================================

engine = create_engine(
    "postgresql+psycopg2://postgres:admin@localhost:5432/gensg_interim_project_g2_db"
)


# ============================================================
# 2. LOAD DENGUE
# ============================================================

dengue = pd.read_sql(
    """
    SELECT
        postal_district,
        location_name,
        case_count,
        "cluster_severity"
    FROM dengue_clusters
    """,
    engine
)


# ============================================================
# 3. LOAD WEATHER
# ============================================================

weather = pd.read_sql(
    """
    SELECT
        area_name,
        record_date,
        total_rainfall_mm
    FROM weather_history
    """,
    engine
)


# ============================================================
# 4. CLEAN DENGUE
# ============================================================

dengue["postal_district"] = (
    dengue["postal_district"]
    .astype(str)
    .str.extract(r"(\d{2})")[0]
)

dengue["case_count"] = pd.to_numeric(
    dengue["case_count"],
    errors="coerce"
).fillna(0)


# ============================================================
# 5. CLEAN WEATHER
# ============================================================

weather["area_name"] = (
    weather["area_name"]
    .astype(str)
    .str.strip()
)

weather["record_date"] = pd.to_datetime(
    weather["record_date"],
    errors="coerce"
)

weather["total_rainfall_mm"] = pd.to_numeric(
    weather["total_rainfall_mm"],
    errors="coerce"
).fillna(0)


# ============================================================
# 6. CURRENT DENGUE CASES BY POSTAL DISTRICT
#
# report_month is NOT USED.
#
# This is your current dengue snapshot.
# ============================================================

dengue_district = (
    dengue
    .groupby("postal_district", as_index=False)
    ["case_count"]
    .sum()
)

print("\n===================================")
print("CURRENT DENGUE BY POSTAL DISTRICT")
print("===================================")

print(
    dengue_district.to_string(index=False)
)


# ============================================================
# 7. DISPLAY THE ACTUAL DENGUE POSTAL DISTRICTS
# ============================================================

print("\n===================================")
print("DENGUE POSTAL DISTRICTS")
print("===================================")

print(
    sorted(
        dengue["postal_district"]
        .dropna()
        .unique()
    )
)


# ============================================================
# 8. WEATHER AREA → POSTAL DISTRICT
#
# We identify the postal district from the area name
# where possible.
#
# This is based on the location name, NOT dengue date.
# ============================================================

def area_to_district(area):

    area = area.lower()


   
        
    # Ang Mo Kio
    if "ang mo kio" in area:
        return "56"

    # Hougang
    elif "hougang" in area:
        return "53"

    # Serangoon
    elif "serangoon" in area:
        return "55"

    # Bedok
    elif "bedok" in area:
        return "46"

    # Tampines
    elif "tampines" in area:
        return "52"

    # Pasir Ris
    elif "pasir ris" in area:
        return "51"

    # Jurong
    elif "jurong" in area:
        return "61"

    # Bukit Batok
    elif "bukit batok" in area:
        return "65"

    # Bukit Panjang
    elif "bukit panjang" in area:
        return "67"

    # Choa Chu Kang
    elif "choa chu kang" in area:
        return "68"

    # Woodlands
    elif "woodlands" in area:
        return "73"

    # Yishun
    elif "yishun" in area:
        return "78"

    # Sembawang
    elif "sembawang" in area:
        return "75"

    # Punggol
    elif "punggol" in area:
        return "80"

    # Pasir Panjang
    elif "pasir panjang" in area:
        return "11"

    # Queenstown
    elif "queenstown" in area:
        return "14"

    # Bukit Timah
    elif "bukit timah" in area:
        return "26"

    # Toa Payoh
    elif "toa payoh" in area:
        return "31"

    # Bishan
    elif "bishan" in area:
        return "57"

    # Clementi
    elif "clementi" in area:
        return "12"

    # Changi
    elif "changi" in area:
        return "48"

    else:
        return None


weather["postal_district"] = weather[
    "area_name"
].apply(area_to_district)


# ============================================================
# 9. SHOW WEATHER MAPPING
# ============================================================

print("\n===================================")
print("WEATHER AREA → POSTAL DISTRICT")
print("===================================")

print(
    weather[
        [
            "area_name",
            "postal_district"
        ]
    ]
    .drop_duplicates()
    .sort_values("area_name")
    .to_string(index=False)
)


# ============================================================
# 10. GET 30-DAY AND 60-DAY WEATHER
# ============================================================

latest_date = weather["record_date"].max()

# ------------------------------------------
# Previous 30 days
# ------------------------------------------

start_30 = latest_date - timedelta(days=30)

weather_30 = weather[
    (weather["record_date"] > start_30)
    &
    (weather["record_date"] <= latest_date)
].copy()


# ------------------------------------------
# Previous 60 days
# ------------------------------------------

start_60 = latest_date - timedelta(days=60)

weather_60 = weather[
    (weather["record_date"] > start_60)
    &
    (weather["record_date"] <= latest_date)
].copy()


# ============================================================
# 11. TOTAL RAINFALL BY POSTAL DISTRICT
# ============================================================

# 30-day rainfall

rainfall_30 = (
    weather_30
    .dropna(subset=["postal_district"])
    .groupby(
        "postal_district",
        as_index=False
    )["total_rainfall_mm"]
    .sum()
    .rename(
        columns={
            "total_rainfall_mm": "rainfall_30_day"
        }
    )
)


# 60-day rainfall

rainfall_60 = (
    weather_60
    .dropna(subset=["postal_district"])
    .groupby(
        "postal_district",
        as_index=False
    )["total_rainfall_mm"]
    .sum()
    .rename(
        columns={
            "total_rainfall_mm": "rainfall_60_day"
        }
    )
)


# ============================================================
# 12. MERGE DENGUE + RAINFALL
# ============================================================

combined_30 = pd.merge(
    dengue_district,
    rainfall_30,
    on="postal_district",
    how="inner"
)


combined_60 = pd.merge(
    dengue_district,
    rainfall_60,
    on="postal_district",
    how="inner"
)


print("\n===================================")
print("30-DAY DATA")
print("===================================")

print(
    combined_30.to_string(index=False)
)


print("\n===================================")
print("60-DAY DATA")
print("===================================")

print(
    combined_60.to_string(index=False)
)


# ============================================================
# 13. POSTAL DISTRICT NAMES
# ============================================================

postal_names = {

    "11": "Pasir Panjang",
    "12": "Clementi",
    "14": "Queenstown",
    "26": "Bukit Timah",
    "31": "Toa Payoh",

    "46": "Bedok",
    "47": "Bedok",
    "48": "Bedok",

    "50": "Tampines",
    "51": "Pasir Ris",
    "52": "Tampines",

    "53": "Hougang",
    "54": "Hougang",
    "55": "Serangoon",

    "56": "Ang Mo Kio",
    "57": "Bishan",

    "60": "Jurong",
    "61": "Jurong",
    "62": "Jurong",
    "63": "Jurong",
    "64": "Jurong",

    "65": "Bukit Batok",
    "66": "Bukit Batok",

    "67": "Bukit Panjang",

    "68": "Choa Chu Kang",
    "69": "Choa Chu Kang",
    "70": "Choa Chu Kang",
    "71": "Choa Chu Kang",

    "72": "Woodlands",
    "73": "Woodlands",
    "74": "Woodlands",

    "75": "Yishun",
    "76": "Yishun",

    "77": "Sembawang",
    "78": "Springleaf / Lentor",

    "79": "Punggol",
    "80": "Seletar",
    "81": "Punggol",
    "82": "Punggol"
}


# ============================================================
# 14. 30-DAY SCATTER PLOT
# ============================================================

plt.figure(figsize=(12, 8))

plt.scatter(
    combined_30["rainfall_30_day"],
    combined_30["case_count"],
    s=120,
    color="green"
)


# Label every point
for _, row in combined_30.iterrows():

    plt.annotate(
        postal_names.get(
            str(row["postal_district"]),
            f"District {row['postal_district']}"
        ),
        (
            row["rainfall_30_day"],
            row["case_count"]
        ),
        xytext=(7, 7),
        textcoords="offset points",
        color="red",
        fontweight="bold",
        fontsize=10
    )


plt.xlabel(
    "Total Rainfall — Previous 30 Days (mm)",
    fontweight="bold"
)

plt.ylabel(
    "Current Dengue Cases",
    fontweight="bold"
)

plt.title(
    "Current Dengue Cases vs Previous 30-Day Rainfall",
    fontweight="bold"
)

plt.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

plt.show()


# ============================================================
# 15. 60-DAY SCATTER PLOT
# ============================================================

plt.figure(figsize=(12, 8))

plt.scatter(
    combined_60["rainfall_60_day"],
    combined_60["case_count"],
    s=120,
    color="green"
)


# Label every point
for _, row in combined_60.iterrows():

    plt.annotate(
        postal_names.get(
            str(row["postal_district"]),
            f"District {row['postal_district']}"
        ),
        (
            row["rainfall_60_day"],
            row["case_count"]
        ),
        xytext=(7, 7),
        textcoords="offset points",
        color="red",
        fontweight="bold",
        fontsize=10
    )


plt.xlabel(
    "Total Rainfall — Previous 60 Days (mm)",
    fontweight="bold"
)

plt.ylabel(
    "Current Dengue Cases",
    fontweight="bold"
)

plt.title(
    "Current Dengue Cases vs Previous 60-Day Rainfall",
    fontweight="bold"
)

plt.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

plt.show()


# Label every point
for _, row in combined.iterrows():


    postal_names = {

    "61": "Jurong",
    "67": "Bukit Panjang",
    "68": "Bukit Panjang",
    "56": "Ang Mo Kio",
    "57": "Ang Mo Kio",
    "53": "Hougang",
    "54": "Hougang",
    "55": "Serangoon",
    "46": "Bedok",
    "47": "Bedok",
    "48": "Bedok",
    "50": "Tampines",
    "51": "Pasir Ris",
    "52": "Tampines",
    "60": "Jurong",
    "61": "Jurong",
    "62": "Jurong",
    "63": "Jurong",
    "64": "Jurong",
    "65": "Bukit Batok",
    "66": "Bukit Batok",
    "69": "Choa Chu Kang",
    "70": "Choa Chu Kang",
    "71": "Choa Chu Kang",
    "72": "Woodlands",
    "73": "Woodlands",
    "74": "Woodlands",
    "75": "Yishun",
    "76": "Yishun",
    "77": "Sembawang",
    "78": "Springleaf/Lentor",
    "79": "Punggol",
    "80": "Punggol",
    "81": "Punggol",
    "82": "Punggol"
}

    plt.annotate(
    postal_names.get(
        str(row["postal_district"]),
        f"District {row['postal_district']}"
    ),
    (
        row["total_rainfall_mm"],
        row["case_count"]
    ),
    xytext=(7, 7),
    textcoords="offset points",
    color="red",
    fontweight="bold",
    fontsize=10
)
    


plt.xlabel(
    "Total Rainfall — Previous 30 Days (mm)"
)

plt.ylabel(
    "Current Dengue Cases"
)

plt.title(
    "Current Dengue Cases vs Previous 30-Day Rainfall"
)

plt.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

plt.show()