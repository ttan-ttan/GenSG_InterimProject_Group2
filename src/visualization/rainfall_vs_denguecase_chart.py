import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# ==========================================
# 1. Connect to PostgreSQL
# ==========================================

engine = create_engine(
    "postgresql+psycopg2://postgres:admin@localhost:5432/gensg_interim_project_g2_db"
)


# ==========================================
# 2. Get historical rainfall data
# ==========================================

df = pd.read_sql("""
    SELECT *
    FROM weather_history
    WHERE record_date >= '2026-07-19'
      AND record_date < '2026-08-20'
""", engine)

# Convert date to datetime
df["record_date"] = pd.to_datetime(df["record_date"])

# Sort by date
df = df.sort_values("record_date")


# ==========================================
# 3. Get today's total dengue cases
# ==========================================

dengue_df = pd.read_sql("""
    SELECT SUM(case_count) AS total_dengue_cases
    FROM dengue_clusters
""", engine)

total_cases = dengue_df["total_dengue_cases"].iloc[0]

print("Today's total dengue cases:", total_cases)


# ==========================================
# 4. Create the chart
# ==========================================

fig, ax1 = plt.subplots(figsize=(14, 7))


# ------------------------------------------
# Rainfall
# ------------------------------------------

ax1.plot(
    df["record_date"],
    df["total_rainfall_mm"],
    marker="o",
    linewidth=2,
    color="red",
    label="Rainfall"
)

ax1.set_xlabel("Date")
ax1.set_ylabel("Rainfall (mm)")

ax1.tick_params(axis="x", rotation=45)


# ------------------------------------------
# Dengue cases
# ------------------------------------------

ax2 = ax1.twinx()

ax2.axhline(
    y=total_cases,
    linewidth=2,
    linestyle="--",
    color="green",
    label=f"Today's Dengue Cases ({total_cases})"
)

ax2.set_ylabel("Total Dengue Cases")


# ==========================================
# 5. Titles
# ==========================================

plt.title(
    "Historical Rainfall vs Today's Total Dengue Cases",
    fontsize=16
)


# ==========================================
# 6. Combine legends
# ==========================================

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()

ax1.legend(
    lines1 + lines2,
    labels1 + labels2,
    loc="upper left"
)


# ==========================================
# 7. Improve layout
# ==========================================



# ==========================================
# 1. Connect to PostgreSQL
# ==========================================

engine = create_engine(
    "postgresql+psycopg2://postgres:admin@localhost:5432/gensg_interim_project_g2_db"
)


# ==========================================
# 2. Get historical rainfall data
# ==========================================

df = pd.read_sql("""
    SELECT *
    FROM weather_history
    WHERE record_date >= '2026-06-19'
      AND record_date < '2026-08-20'
""", engine)

# Convert date to datetime
df["record_date"] = pd.to_datetime(df["record_date"])

# Sort by date
df = df.sort_values("record_date")


# ==========================================
# 3. Get today's total dengue cases
# ==========================================

dengue_df = pd.read_sql("""
    SELECT SUM(case_count) AS total_dengue_cases
    FROM dengue_clusters
""", engine)

total_cases = dengue_df["total_dengue_cases"].iloc[0]

print("Today's total dengue cases:", total_cases)


# ==========================================
# 4. Create the chart
# ==========================================

fig, ax1 = plt.subplots(figsize=(14, 7))


# ------------------------------------------
# Rainfall
# ------------------------------------------

ax1.plot(
    df["record_date"],
    df["total_rainfall_mm"],
    marker="o",
    color="red",
    linewidth=2,
    label="Rainfall"
)

ax1.set_xlabel("Date")
ax1.set_ylabel("Rainfall (mm)")

ax1.tick_params(axis="x", rotation=45)


# ------------------------------------------
# Dengue cases
# ------------------------------------------

ax2 = ax1.twinx()

ax2.axhline(
    y=total_cases,
    linewidth=2,
    linestyle="--",
    color="green",
    label=f"Today's Dengue Cases ({total_cases})"
)

ax2.set_ylabel("Total Dengue Cases")


# ==========================================
# 5. Titles
# ==========================================

plt.title(
    "Historical Rainfall vs Today's Total Dengue Cases",
    fontsize=16
)


# ==========================================
# 6. Combine legends
# ==========================================

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()

ax1.legend(
    lines1 + lines2,
    labels1 + labels2,
    loc="upper left"
)


# ==========================================
# 7. Improve layout
# ==========================================

fig.tight_layout()

plt.show()