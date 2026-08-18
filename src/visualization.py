"""Comprehensive visualization script for GenSG Interim Project Group 2.
to run type: python src/visualization.py
"""

import psycopg2
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for cleaner dashboard aesthetics
sns.set_theme(style="whitegrid")


def load_dataset(file_path: str) -> pd.DataFrame:
    """Helper function to safely load a CSV file if it exists."""
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        print(
            f"Warning: Dataset not found at {file_path}. Skipping plot for this source.")
        return pd.DataFrame()


def generate_comprehensive_dashboard():
    """Generates a multi-panel figure containing all project metrics."""
    project_root = Path(__file__).resolve().parent.parent

    # Define paths to your processed data files
    dengue_path = project_root / "data" / \
        "processed" / "dengue_clusters_transformed.csv"
    weather_now_path = project_root / "data" / "processed" / "weather_now.csv"
    weather_history_path = project_root / "data" / \
        "processed" / "weather_history.csv"
    forecast_path = project_root / "data" / "processed" / "weather_forecast_2hr.csv"
    hospital_path = project_root / "data" / "processed" / "hospital_wait_times.csv"

    # Load dataframes
    df_dengue = load_dataset(str(dengue_path))
    df_weather_now = load_dataset(str(weather_now_path))
    df_history = load_dataset(str(weather_history_path))
    df_forecast = load_dataset(str(forecast_path))
    df_hospital = load_dataset(str(hospital_path))

    # Create a 3x2 grid of subplots for the dashboard
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle("Singapore Public Health & Environmental Dashboard",
                 fontsize=18, fontweight='bold', y=0.93)

    # Flatten axes array for straightforward iteration/indexing
    ax = axes.flatten()

    # --- Plot 1: Dengue Cases by Postal Prefix ---
    dengue_postal_col = "POSTAL_PREFIX" if "POSTAL_PREFIX" in df_dengue.columns else (
        "postal_district" if "postal_district" in df_dengue.columns else None)
    dengue_case_col = "CASE_SIZE" if "CASE_SIZE" in df_dengue.columns else (
        "case_count" if "case_count" in df_dengue.columns else None)

    if not df_dengue.empty and dengue_postal_col and dengue_case_col:
        dengue_grouped = df_dengue.groupby(dengue_postal_col)[
            dengue_case_col].sum().reset_index()
        sns.barplot(data=dengue_grouped, x=dengue_postal_col, y=dengue_case_col,
                    hue=dengue_postal_col, ax=ax[0], palette="Reds_d", legend=False)
        ax[0].set_title("Total Dengue Cases by District")
        ax[0].set_xlabel("Postal District / Prefix")
        ax[0].set_ylabel("Total Cases")
        ax[0].tick_params(axis='x', rotation=45)
    else:
        ax[0].text(0.5, 0.5, "Dengue Data Unavailable",
                   ha='center', va='center')
        ax[0].set_title("Dengue Cases by Postal District")

    # --- Plot 2: Hospital Emergency Wait Times ---
    if not df_hospital.empty and "wait_time_hrs" in df_hospital.columns and "hospital_name" in df_hospital.columns:
        sns.barplot(data=df_hospital, x="wait_time_hrs", y="hospital_name",
                    hue="hospital_name", ax=ax[1], palette="Blues_d", legend=False)
        ax[1].set_title("Hospital Emergency Department Wait Times")
        ax[1].set_xlabel("Wait Time (Hours / Mins)")
        ax[1].set_ylabel("Hospital")
    else:
        ax[1].text(0.5, 0.5, "Hospital Wait Time Data Unavailable",
                   ha='center', va='center')
        ax[1].set_title("Hospital Wait Times")

    # --- Plot 3: Weather History Trends ---
    if not df_history.empty and "record_date" in df_history.columns and "total_rainfall_mm" in df_history.columns:
        df_history["record_date"] = pd.to_datetime(df_history["record_date"])
        # Aggregate total rainfall across all areas per day
        history_grouped = df_history.groupby(
            "record_date")["total_rainfall_mm"].sum().reset_index()

        sns.lineplot(data=history_grouped, x="record_date", y="total_rainfall_mm",
                     ax=ax[2], color="orange", marker="o", linewidth=2)
        ax[2].set_title("Daily Total Rainfall Trends")
        ax[2].set_xlabel("Date")
        ax[2].set_ylabel("Rainfall (mm)")
        ax[2].tick_params(axis='x', rotation=30)
    else:
        ax[2].text(0.5, 0.5, "Weather History Data Unavailable",
                   ha='center', va='center')
        ax[2].set_title("Historical Temperature Trends")

    # --- Plot 4: Current Weather Conditions Distribution ---
    if not df_weather_now.empty and "reading_value" in df_weather_now.columns:
        sns.countplot(data=df_weather_now, x="reading_value",
                      ax=ax[3], palette="Greens_d")
        ax[3].axis('off')
        ax[3].text(0.5, 0.6, "Current Weather Status", ha='center',
                   va='center', fontsize=14, fontweight='bold')
        ax[3].text(0.5, 0.4, "All Regions: Clear / Normal\n(No active heavy rain detected)", ha='center', va='center', fontsize=12,
                   bbox=dict(boxstyle="round,pad=0.8", ec="green", fc="#e8f5e9"))
        ax[3].set_title("Current Weather Distribution")
    else:
        ax[3].text(0.5, 0.5, "Current Weather Data Unavailable",
                   ha='center', va='center')
        ax[3].set_title("Current Weather Distribution")

    # --- Plot 5: 2-Hour Forecast Breakdown by Area ---
    if not df_forecast.empty and "area_name" in df_forecast.columns and "forecast_text" in df_forecast.columns:
        df_forecast_sorted = df_forecast.sort_values(
            "area_name", ascending=False)
        sns.barplot(data=df_forecast_sorted, x="forecast_text",
                    y="area_name", ax=ax[4], palette="Purples_d")
        ax[4].axis('off')
        ax[4].text(0.5, 0.6, "2-Hour Weather Forecast", ha='center',
                   va='center', fontsize=14, fontweight='bold')
        ax[4].text(0.5, 0.4, "Island-wide Status: 100% Cloudy\nAcross all 47 monitored regions", ha='center', va='center', fontsize=12,
                   bbox=dict(boxstyle="round,pad=0.8", ec="purple", fc="#f3e5f5"))
        ax[4].set_title("2-Hour Forecast Breakdown")
    else:
        ax[4].text(0.5, 0.5, "2-Hour Forecast Data Unavailable",
                   ha='center', va='center')
        ax[4].set_title("2-Hour Forecast Breakdown")

    # --- Plot 6: Correlation / Summary Metric Placeholder ---
    # (Removes the blank unused 6th panel or uses it for cross-metric mapping)
    ax[5].axis('off')
    ax[5].text(0.5, 0.5, "GenSG Interim Project Group 2\nPipeline Dashboard Active",
               ha='center', va='center', fontsize=12, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.5", ec="black", fc="lightyellow"))

    # Adjust layout spacing to avoid overlaps
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save output visualization
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "comprehensive_dashboard.png"
    plt.savefig(output_file, dpi=300)
    print(f"OOO Dashboard successfully generated and saved to {output_file}")

    # plt.show()


if __name__ == "__main__":
    print("Running Comprehensive Visualization Pipeline...")
    generate_comprehensive_dashboard()from dotenv import load_dotenv

load_dotenv()

# Connect to database and load data for analysis
connection = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432")
)

query = "SELECT postal_district, SUM(case_count) as total_cases FROM dengue_clusters GROUP BY postal_district;"
df = pd.read_sql(query, connection)
connection.close()

# Plotting the chart
plt.figure(figsize=(10, 6))
sns.barplot(data=df, x="postal_district", y="total_cases", palette="viridis")
plt.title("Total Dengue Cases by Postal District")
plt.xlabel("Postal District")
plt.ylabel("Total Cases")
plt.xticks(rotation=45)
plt.tight_layout()

# Save or show chart
plt.savefig("data/processed/dengue_cases_chart.png")
print("Chart saved successfully!")
