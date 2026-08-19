"""Main execution script for patient emergency hospital routing recommendation

and automated data pipeline controller.
"""

# Standard library imports
import os
from pathlib import Path
import subprocess
import sys
from dotenv import load_dotenv
import psycopg2
from src.routing_logic import evaluate_hospitals_for_patient

# First-party imports (adjust path so local package imports work cleanly)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()


def reset_database_schema():
    """Explicitly drops and recreates all database tables using the DDL schema file."""
    confirm = input(
        "WARNING: This will ERASE all stored data and reset tables! "
        "Are you sure? (y/n): "
    ).strip().lower()

    if confirm != 'y':
        print("Reset cancelled.")
        return

    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "doc" / "database_schema.sql"

    if not schema_path.exists():
        print(f"XXX Error: Schema file not found at {schema_path}")
        return

    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

        with connection.cursor() as cursor:
            with open(schema_path, "r", encoding="utf-8") as f:
                ddl_script = f.read()
            cursor.execute(ddl_script)
            connection.commit()

        connection.close()
        print("OOO Successfully dropped and recreated tables from schema!")

    except psycopg2.Error as e:
        print(f"XXX Database error during schema reset: {e}")


def run_full_pipeline():
    """Triggers the complete multi-source ETL pipeline,

    updates visualizations, and opens the output image.
    """
    print(
        "\n================ Executing Full Multi-Source ETL Pipeline ================"
    )
    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "src"

    try:
        # --- 1. TRANSFORM & EXTRACT STAGE ---
        pipeline_scripts = [
            src_dir / "transform" / "transform_dangue.py",
            src_dir / "transform" / "transform_realtime_weather.py",
            src_dir / "transform" / "transform_history_weather.py",
            src_dir / "transform" / "transform_forecast_weather.py",
            src_dir / "transform" / "transform_hospital_time.py",
        ]

        for script in pipeline_scripts:
            if os.path.exists(script):
                print(f"-> Running: {script.relative_to(project_root)}")
                result = subprocess.run(
                    [sys.executable, str(script)], check=False
                )
                if result.returncode != 0:
                    print(
                        f"XXX Warning/Error in script: {script.name}. Continuing..."
                    )
            else:
                print(f"--- Notice: Script not found, skipping: {script.name}")

        # --- 2. LOAD STAGE ---
        print("\n-> Loading all domains into PostgreSQL database...")
        load_scripts = [
            src_dir / "load" / "load_dangue.py",
            src_dir / "load" / "load_realtime_weather.py",
            src_dir / "load" / "load_history_weather.py",
            src_dir / "load" / "load_forecast_weather.py",
            src_dir / "load" / "load_hospital_time.py",
        ]

        for script in load_scripts:
            if os.path.exists(script):
                print(f"-> Loading: {script.relative_to(project_root)}")
                result = subprocess.run(
                    [sys.executable, str(script)], check=False
                )
                if result.returncode != 0:
                    print(
                        f"XXX Warning/Error in loader: {script.name}. "
                        "Continuing..."
                    )
            else:
                print(
                    f"--- Notice: Loader script not found, skipping: {script.name}"
                )

        # --- 3. VISUALIZATION STAGE ---
        print("\n-> Generating comprehensive project dashboard visualization...")
        viz_script = src_dir / "visualization.py"
        if os.path.exists(viz_script):
            result = subprocess.run(
                [sys.executable, str(viz_script)], check=False)
            if result.returncode != 0:
                print("XXX Error: Visualization script failed.")
                return
        else:
            print("--- Error: visualization.py not found.")
            return

        # --- 4. OPEN THE GENERATED DASHBOARD IMAGE ---
        chart_path = (
            project_root / "data" / "processed" / "comprehensive_dashboard.png"
        )
        if not chart_path.exists():
            chart_path = (
                project_root / "data" / "processed" / "dengue_cases_chart.png"
            )

        if chart_path.exists():
            print(f"OOO Success! Opening dashboard chart: {chart_path}")
            if sys.platform == "win32":
                os.startfile(str(chart_path))
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(chart_path)], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", str(chart_path)], check=False)
        else:
            print(
                f"XXX Warning: Dashboard chart file could not be located at {chart_path}"
            )

    except (subprocess.SubprocessError, OSError) as pipeline_err:
        print(f"XXX Error during full pipeline execution: {pipeline_err}")
    print("=========================================================================\n")


def handle_hospital_routing():
    """Handles the interactive hospital emergency routing workflow."""
    print(
        "\n=========== Singapore A&E Hospital Routing System (< 30 Mins Filter) ============"
    )

    user_postal = input("Enter your 6-digit postal code: ").strip()

    if len(user_postal) != 6 or not user_postal.isdigit():
        print(
            "XXX Error: Invalid postal code format. "
            "Please enter a 6-digit numeric postal code."
        )
        return

    hospitals_dataset = [
        {
            "name": "Singapore General Hospital (SGH)",
            "base_travel_time_mins": 18.0,
            "waiting_time_mins": 45,
        },
        {
            "name": "Tan Tock Seng Hospital (TTSH)",
            "base_travel_time_mins": 12.0,
            "waiting_time_mins": 60,
        },
        {
            "name": "Khoo Teck Puat Hospital (KTPH)",
            "base_travel_time_mins": 25.0,
            "waiting_time_mins": 30,
        },
        {
            "name": "National University Hospital (NUH)",
            "base_travel_time_mins": 28.0,
            "waiting_time_mins": 50,
        },
        {
            "name": "Changi General Hospital (CGH)",
            "base_travel_time_mins": 32.0,
            "waiting_time_mins": 25,
        },
    ]

    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )

        print(f"\nAnalyzing routes for Postal Prefix '{user_postal[:2]}'...")

        evaluation_result = evaluate_hospitals_for_patient(
            user_postal, hospitals_dataset, connection
        )

        connection.close()

        print(f"-> Mapped Region: {evaluation_result['patient_region']}")
        print(
            f"-> Weather Status (Rain Forecasted): {evaluation_result['will_rain']}\n"
        )

        best_choice = evaluation_result["best_choice"]
        recommendations = evaluation_result["recommendations"]

        if not best_choice:
            print(
                "XXXXXXXXXXXXXXXXXXXXX No hospitals found within the "
                "30-minute travel threshold under current conditions.XXXXXXXXXXXXXXX"
            )
        else:
            print("                        Best Hospital to Go:")
            print(
                f"-----------------------{best_choice['hospital_name']}------------------------------"
            )
            print(
                f"                    Total Time to Treatment: {best_choice['total_time']} mins "
                f"(Travel: {best_choice['travel_time']}m + Wait: {best_choice['waiting_time']}m)"
            )
            if best_choice['weather_impact']:
                print(
                    f"   - Active Delays: {', '.join(best_choice['weather_impact'])}"
                )
            print("-" * 83)

            print("\n All Valid Alternative Options (Sorted by Fastest Total Time):")
            for idx, rec in enumerate(recommendations, 1):
                print(f"{idx}. {rec['hospital_name']}")
                print(
                    f"   - Travel Time: {rec['travel_time']} mins | "
                    f"A&E Wait: {rec['waiting_time']} mins | Total: {rec['total_time']} mins"
                )
                if rec['weather_impact']:
                    print(f"   - Factors: {', '.join(rec['weather_impact'])}")
                print()
            print(
                "=================== MAI TU LIAO KAH GIN GO HOSPITAL!!==============================="
            )

    except psycopg2.Error as db_err:
        print(f"XXX Database connection failed: {db_err}")


def main():
    """Main menu interface control loop."""
    while True:
        print("\n=================== GenSG Project Main Menu ===================")
        print("[1] Run Full ETL Pipeline, Update Visualizations & View Dashboard")
        print("[2] Search Emergency Hospital Routing Recommendation")
        print("[3] Reset/Recreate Database Schema (⚠️ Wipes all data)")
        print("[0] Exit")

        choice = input("Select an option (0-3): ").strip()

        if choice == "1":
            run_full_pipeline()
        elif choice == "2":
            handle_hospital_routing()
        elif choice == "3":
            reset_database_schema()
        elif choice == "0":
            print("Exiting application. Stay safe!")
            break
        else:
            print("XXX Invalid option. Please choose 0, 1, 2, or 3.")


if __name__ == "__main__":
    main()
