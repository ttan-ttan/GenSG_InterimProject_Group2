"""Routing logic module for calculating hospital travel times under 30 minutes, 
incorporating weather, peak hour traffic penalties, and optimizing for 
earliest total time-to-treatment (Travel + A&E Wait Time).
"""

from datetime import datetime


def get_region_from_postal(postal_code: str) -> str:
    """Maps the first 2 digits of a Singapore postal code to a general region/area name."""
    if not postal_code or len(postal_code) < 2:
        return "Unknown"

    prefix = postal_code[:2]

    # Simplified mapping of Singapore postal districts to general regions
    mapping = {
        ("01", "02", "03", "04", "05", "06"): "Central Area",
        ("07", "08"): "Marina South",
        ("14", "15", "16"): "Queenstown",
        ("10", "11", "12", "13"): "Clementi",
        ("19", "20", "21"): "Bishan",
        ("22", "23", "24", "25", "26", "27"): "Orchard",
        ("28", "29", "30", "31", "32", "33"): "Toa Payoh",
        ("34", "35", "36", "37"): "MacPherson",
        ("38", "39", "40", "41"): "Geylang",
        ("42", "43", "44", "45"): "Katong",
        ("46", "47", "48"): "Bedok",
        ("49", "50", "81"): "Changi",
        ("51", "52"): "Pasir Ris",
        ("53", "54", "55", "82"): "Punggol",
        ("56", "57"): "Ang Mo Kio",
        ("58", "59"): "Yio Chu Kang",
        ("60", "61", "62", "63", "64"): "Jurong",
        ("65", "66", "67", "68"): "Bukit Batok",
        ("69", "70", "71"): "Sungei Kadut",
        ("72", "73"): "Woodlands",
        ("75", "76"): "Yishun",
        ("77", "78"): "Sembawang",
        ("79", "80"): "Seletar",
    }

    for prefixes, region in mapping.items():
        if prefix in prefixes:
            return region

    return "Central Area"  # Default fallback


def is_peak_hour(current_time: datetime = None) -> tuple[bool, float]:
    """Checks if current time falls under morning or evening peak traffic periods.
    Returns a tuple of (is_peak_bool, penalty_multiplier).
    """
    if current_time is None:
        current_time = datetime.now()

    hour = current_time.hour
    minute = current_time.minute
    time_val = hour + minute / 60.0

    # Morning peak: 07:30 to 09:30 (+30% delay)
    if 7.5 <= time_val <= 9.5:
        return True, 1.30

    # Evening peak: 17:30 to 20:00 (+35% delay)
    if 17.5 <= time_val <= 20.0:
        return True, 1.35

    return False, 1.00


def calculate_adjusted_travel_time(
    base_time_minutes: float,
    will_rain: bool,
    current_time: datetime = None
) -> dict:
    """Calculates final estimated travel time considering weather and traffic penalties,
    plus fixed operational buffers (e.g., parking/drop-off).
    """
    if current_time is None:
        current_time = datetime.now()

    multiplier = 1.0
    factors_applied = []

    # 1. Weather Penalty (Rain causes slower traffic speeds, ~20% increase)
    if will_rain:
        multiplier += 0.20
        factors_applied.append("Rain Congestion (+20%)")

    # 2. Peak Hour Traffic Penalty
    is_peak, peak_multiplier = is_peak_hour(current_time)
    if is_peak:
        multiplier *= peak_multiplier
        factors_applied.append(
            f"Peak Hour Traffic ({int((peak_multiplier - 1) * 100)}%)")

    # 3. Fixed operational buffer (3-minute buffer for A&E drop-off and parking)
    fixed_buffer_minutes = 3.0

    final_travel_time = (base_time_minutes * multiplier) + fixed_buffer_minutes

    return {
        "base_time": base_time_minutes,
        "final_estimated_time": round(final_travel_time, 1),
        "is_under_30_mins": final_travel_time <= 30.0,
        "factors": factors_applied
    }


def evaluate_hospitals_for_patient(
    postal_code: str,
    conn
) -> dict:
    """Queries live hospital wait times from the database, evaluates them against 
    the patient's postal code region, factors in weather and traffic, filters out 
    choices exceeding 30 minutes, and ranks them by total time-to-treatment.
    """
    patient_region = get_region_from_postal(postal_code)
    valid_recommendations = []

    with conn.cursor() as cursor:
        # 1. Query the latest weather forecast for the patient's mapped region
        cursor.execute(
            "SELECT will_rain FROM weather_forecast WHERE area_name ILIKE %s",
            (f"%{patient_region}%",)
        )
        row = cursor.fetchone()
        will_rain = row[0] if row else False

        # 2. Query the latest snapshot of all monitored hospitals from database scrapers/mock data
        cursor.execute("""
            SELECT DISTINCT ON (hospital_name)
                hospital_name,
                wait_time_hrs,
                patients_waiting_count,
                doctor_wait_minutes
            FROM hospital_wait_times
            ORDER BY hospital_name, updated_at DESC;
        """)
        db_hospitals = cursor.fetchall()

    # Fallback default base travel times (in minutes) for standard Singapore hospitals
    # if dynamic mapping isn't fully configured per postal district yet
    default_base_travel_times = {
        "Singapore General Hospital (SGH)": 18.0,
        "Tan Tock Seng Hospital (TTSH)": 12.0,
        "Khoo Teck Puat Hospital (KTPH)": 25.0,
        "National University Hospital (NUH)": 28.0,
        "Changi General Hospital (CGH)": 32.0,
        "Ng Teng Fong General Hospital (NTFGH)": 26.0,
        "Sengkang General Hospital (SKH)": 24.0,
        "Alexandra Hospital": 15.0
    }

    for hosp_row in db_hospitals:
        name = hosp_row[0]
        wait_time_hrs = float(hosp_row[1]) if hosp_row[1] is not None else 1.0

        waiting_time_mins = int(wait_time_hrs * 60)
        base_time = default_base_travel_times.get(name, 20.0)

        # Compute travel time with modifiers (Weather + Traffic + Buffer)
        travel_result = calculate_adjusted_travel_time(base_time, will_rain)

        total_time_to_treatment = travel_result["final_estimated_time"] + \
            waiting_time_mins

        # AMENDED: Include all hospitals in ranking, but keep the flag
        # to show if it's within the preferred 30-min travel window.
        valid_recommendations.append({
            "hospital_name": name,
            "travel_time": travel_result["final_estimated_time"],
            "waiting_time": waiting_time_mins,
            "total_time": total_time_to_treatment,
            "weather_impact": travel_result["factors"],
            "is_under_30_mins": travel_result["is_under_30_mins"]
        })

    # Sort recommendations by the fastest total time (Travel + Wait Time)
    valid_recommendations.sort(key=lambda x: x["total_time"])

    best_choice = valid_recommendations[0] if valid_recommendations else None

    # Restrict alternatives to only the next top 2 fastest choices
    alternatives = valid_recommendations[1:3] if len(
        valid_recommendations) > 1 else []

    return {
        "patient_region": patient_region,
        "will_rain": will_rain,
        "recommendations": alternatives,
        "best_choice": best_choice
    }
