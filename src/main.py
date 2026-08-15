"""The main module to execute the emergency routing application workflow."""

import requests
from .routing_logic import (
    get_base_travel_times_by_postal,
    calculate_total_time_to_treatment,
    evaluate_routing_decision
)
from .predict_wait_times import forecast_hospital_wait_time


def check_weather_condition() -> bool:
    """
    Fetches real-time weather from data.gov.sg to check for heavy rain.
    Returns True if heavy rain/showers are detected, else False.
    """
    url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                for forecast in item.get("forecasts", []):
                    text = forecast.get("forecast", "").lower()
                    if "rain" in text or "shower" in text or "thundery" in text:
                        return True
        print(
            "[Weather API]: Clear skies or API unavailable. "
            "Defaulting to normal traffic."
        )
        return False
    except requests.exceptions.RequestException as e:
        print(
            f"[Weather API Notice]: Could not fetch live weather ({e}). "
            "Proceeding with standard traffic."
        )
        return False


def main():
    """Run the main emergency routing application workflow."""
    print("==================================================")
    print("   SMART-ROUTE ED: Emergency Load Balancer System  ")
    print("==================================================")

    # 1. Get User Input
    user_postal = input(
        "Enter your 6-digit Singapore Postal Code (e.g., 520123): "
    ).strip()

    hospital_travel_map = get_base_travel_times_by_postal(user_postal)

    if not hospital_travel_map:
        print("❌ Error: Invalid postal code format. Please enter exactly 6 digits.")
        return

    print(
        f"✔ Location Detected: Sector prefix {user_postal[:2]} loaded successfully.")

    # 2. Check Live Weather
    print("⏳ Checking live weather conditions via data.gov.sg...")
    is_heavy_rain = check_weather_condition()
    print(f"✔ Heavy Rain Status: {is_heavy_rain}")

    # 3. Predict/Fetch Hospital Wait Times
    nuh_base_wait = forecast_hospital_wait_time(
        "National University Hospital (NUH)", 3.2
    )
    ntf_base_wait = forecast_hospital_wait_time(
        "Ng Teng Fong General Hospital (NTFGH)", 1.2
    )
    ttsh_base_wait = forecast_hospital_wait_time(
        "Tan Tock Seng Hospital (TTSH)", 4.5
    )
    cgh_base_wait = forecast_hospital_wait_time(
        "Changi General Hospital (CGH)", 1.5
    )

    hospitals_db = [
        {
            "hospital_name": "National University Hospital (NUH)",
            "wait_time_hrs": nuh_base_wait
        },
        {
            "hospital_name": "Ng Teng Fong General Hospital (NTFGH)",
            "wait_time_hrs": ntf_base_wait
        },
        {
            "hospital_name": "Tan Tock Seng Hospital (TTSH)",
            "wait_time_hrs": ttsh_base_wait
        },
        {
            "hospital_name": "Changi General Hospital (CGH)",
            "wait_time_hrs": cgh_base_wait
        }
    ]

    # 4. Calculate Total Time to Treatment using routing_logic.py
    print("\n--------------------------------------------------")
    print("Computing Total Time to Treatment (Travel + Wait)...")
    print("--------------------------------------------------")

    sorted_hospitals = calculate_total_time_to_treatment(
        hospital_travel_map, hospitals_db, is_heavy_rain
    )
    nearest, second_nearest, time_difference, should_divert = (
        evaluate_routing_decision(sorted_hospitals)
    )

    print("1st Choice:", nearest['hospital'])
    print(
        f"    -> Travel Time: {nearest['final_travel_mins']} mins | "
        f"Wait Time: {nearest['wait_time_hrs']} hrs | "
        f"Total: {nearest['total_time_mins']} mins"
    )

    print("2nd Choice:", second_nearest['hospital'])
    print(
        f"    -> Travel Time: {second_nearest['final_travel_mins']} mins | "
        f"Wait Time: {second_nearest['wait_time_hrs']} hrs | "
        f"Total: {second_nearest['total_time_mins']} mins"
    )

    # 5. Final Recommendation Output
    print("\n================ FINAL RECOMMENDATION ================")
    if should_divert:
        print(f"🚨 DIVERT RECOMMENDATION: Go to {second_nearest['hospital']}!")
        print(
            f"💡 Reason: Even though it is further away, you save {time_difference} "
            "minutes overall because the nearest hospital is heavily congested."
        )
    else:
        print(f"✅ STANDARD RECOMMENDATION: Go to {nearest['hospital']}.")
        print(
            "💡 Reason: The time saved by traveling further does not "
            "offset the extra transit time."
        )
    print("=======================================================")


if __name__ == "__main__":
    main()
