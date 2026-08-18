"""Main execution script for patient emergency hospital routing recommendation."""

from src.routing_logic import evaluate_hospitals_for_patient
from pathlib import Path
import os
import sys

from dotenv import load_dotenv
import psycopg2

# Go up one level to reach root, then point to src folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


load_dotenv()


def main():
    """Executes the main CLI workflow for hospital routing based on user location and live conditions."""
    print("=========== Singapore A&E Hospital Routing System (< 30 Mins Filter) ============")

    # User Input
    user_postal = input("Enter your 6-digit postal code: ").strip()

    if len(user_postal) != 6 or not user_postal.isdigit():
        print("XXX Error: Invalid postal code format. Please enter a 6-digit numeric postal code.")
        return

    # Sample mock hospital list (In production, base travel times come from a distance matrix API
    # and waiting times come from your live database tables)
    hospitals_dataset = [
        {
            "name": "Singapore General Hospital (SGH)",
            "base_travel_time_mins": 18.0,
            "waiting_time_mins": 45
        },
        {
            "name": "Tan Tock Seng Hospital (TTSH)",
            "base_travel_time_mins": 12.0,
            "waiting_time_mins": 60
        },
        {
            "name": "Khoo Teck Puat Hospital (KTPH)",
            "base_travel_time_mins": 25.0,
            "waiting_time_mins": 30
        },
        {
            "name": "National University Hospital (NUH)",
            "base_travel_time_mins": 28.0,
            "waiting_time_mins": 50
        },
        {
            "name": "Changi General Hospital (CGH)",
            "base_travel_time_mins": 32.0,
            "waiting_time_mins": 25
        },  # Filtered out (>30 min)
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

        # Evaluate hospitals using routing logic
        evaluation_result = evaluate_hospitals_for_patient(
            user_postal, hospitals_dataset, connection
        )

        connection.close()

        print(f"-> Mapped Region: {evaluation_result['patient_region']}")
        print(
            f"-> Weather Status (Rain Forecasted): {evaluation_result['will_rain']}\n")

        # Display Top Proposal
        best_choice = evaluation_result["best_choice"]
        recommendations = evaluation_result["recommendations"]

        if not best_choice:
            print(
                "XXXXXXXXXXXXXXXXXXXXX No hospitals found within the 30-minute travel threshold under current conditions.XXXXXXXXXXXXXXX")
        else:
            print("                          Best Hospital to Go:")
            print(
                f"-----------------------{best_choice['hospital_name']}------------------------------")
            print(
                f"              Total Time to Treatment: {best_choice['total_time']} mins "
                f"(Travel: {best_choice['travel_time']}m + Wait: {best_choice['waiting_time']}m)"
            )
            if best_choice['weather_impact']:
                print(
                    f"   - Active Delays: {', '.join(best_choice['weather_impact'])}")
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
                "=================== MAI TU LIAO KAH GIN GO HOSPITAL!!===============================")
    except psycopg2.Error as db_err:
        print(f"XXX Database connection failed: {db_err}")


if __name__ == "__main__":
    main()


# to run this scrypt, type in terminal: python -m src.main
