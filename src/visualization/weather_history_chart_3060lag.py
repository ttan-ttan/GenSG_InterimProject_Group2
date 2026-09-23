import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Connect to PostgreSQL
engine = create_engine(
    "postgresql+psycopg2://postgres:admin@localhost:5432/gensg_interim_project_g2_db"
)

# Get weather history from PostgreSQL
df = pd.read_sql("""
    SELECT *
    FROM weather_history
    WHERE record_date >= '2026-07-19'
      AND record_date < '2026-08-20'
""", engine)

# Check data
print(df.head())
print(df.columns)
print("Number of rows:", len(df))

# Convert date
df["record_date"] = pd.to_datetime(df["record_date"])

# Sort by date
df = df.sort_values("record_date")

# Plot rainfall
plt.figure(figsize=(12, 6))

plt.plot(
    df["record_date"],
    df["total_rainfall_mm"],
    marker="o",
    color="red"
)

plt.title("Historical Rainfall — 19 Jul to 19 Aug 2026")
plt.xlabel("Date")
plt.ylabel("Total Rainfall (mm)")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

# Get weather history from PostgreSQL
df = pd.read_sql("""
    SELECT *
    FROM weather_history
    WHERE record_date >= '2026-06-19'
      AND record_date < '2026-08-20'
""", engine)

# Check data
print(df.head())
print(df.columns)
print("Number of rows:", len(df))

# Convert date
df["record_date"] = pd.to_datetime(df["record_date"])

# Sort by date
df = df.sort_values("record_date")

# Plot rainfall
plt.figure(figsize=(12, 6))

plt.plot(
    df["record_date"],
    df["total_rainfall_mm"],
    marker="o",
    color="red"
)


plt.title("Historical Rainfall — 19 Jun to 19 Aug 2026")
plt.xlabel("Date")
plt.ylabel("Total Rainfall (mm)")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

