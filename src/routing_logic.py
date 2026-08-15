"""Module containing the core routing and distance calculation logic based on travel time blocks."""


def get_base_travel_times_by_postal(postal_code: str) -> dict:
    """
    Maps a 6-digit Singapore postal code prefix to baseline travel times (in minutes) 
    for each hospital based on approximate 5-10 min distance sectors.
    """
    if not postal_code or not postal_code.isdigit() or len(postal_code) != 6:
        return None

    prefix = int(postal_code[:2])

    # Example baseline travel time mapping based on postal district/prefix sectors
    # (Adjust these values based on your exact hospital coordinates/distance data)
    if prefix in [1, 2, 3, 4, 5, 6, 7, 8]:  # Central / Downtown
        return {
            "National University Hospital (NUH)": 15,
            "Ng Teng Fong General Hospital (NTFGH)": 20,
            "Tan Tock Seng Hospital (TTSH)": 10,
            "Changi General Hospital (CGH)": 25
        }
    elif prefix in [58, 59, 60, 61, 62, 63, 64]:  # Far West (Jurong/Clementi)
        return {
            "National University Hospital (NUH)": 12,
            "Ng Teng Fong General Hospital (NTFGH)": 8,
            "Tan Tock Seng Hospital (TTSH)": 30,
            "Changi General Hospital (CGH)": 45
        }
    elif prefix in [46, 47, 48, 49, 50]:  # East (Bedok/Tampines/Changi)
        return {
            "National University Hospital (NUH)": 35,
            "Ng Teng Fong General Hospital (NTFGH)": 40,
            "Tan Tock Seng Hospital (TTSH)": 25,
            "Changi General Hospital (CGH)": 10
        }
    else:  # Default fallback for other sectors (North / North-East)
        return {
            "National University Hospital (NUH)": 25,
            "Ng Teng Fong General Hospital (NTFGH)": 30,
            "Tan Tock Seng Hospital (TTSH)": 15,
            "Changi General Hospital (CGH)": 30
        }


def calculate_total_time_to_treatment(
    hospital_travel_map: dict, hospitals_db: list, is_heavy_rain: bool
) -> list:
    """
    Computes travel time using micro-location baselines, applies weather traffic delay 
    multipliers if necessary, converts wait time hours into minutes, and returns a sorted list.
    """
    processed_hospitals = []

    for h in hospitals_db:
        hospital_name = h["hospital_name"]

        # Pull the specific baseline travel time for this hospital based on user's postal prefix
        base_travel = hospital_travel_map.get(
            hospital_name, 20)  # Default to 20 mins if missing

        # Apply heavy rain traffic penalty to travel time (+25% delay)
        if is_heavy_rain:
            final_travel = round(base_travel * 1.25, 1)
        else:
            final_travel = base_travel

        # Convert wait time from hours to minutes
        wait_mins = h["wait_time_hrs"] * 60
        total_time = round(final_travel + wait_mins, 1)

        processed_hospitals.append({
            "hospital": hospital_name,
            "base_travel_mins": base_travel,
            "final_travel_mins": final_travel,
            "wait_time_hrs": h["wait_time_hrs"],
            "total_time_mins": total_time
        })

    # Sort hospitals by total time (ascending: fastest total time first)
    sorted_hospitals = sorted(
        processed_hospitals, key=lambda x: x["total_time_mins"]
    )
    return sorted_hospitals


def evaluate_routing_decision(sorted_hospitals: list):
    """
    Evaluates whether a diversion to the second-best choice is recommended 
    based on overall time savings.
    """
    nearest = sorted_hospitals[0]
    second_nearest = sorted_hospitals[1]

    time_difference = round(
        abs(nearest["total_time_mins"] - second_nearest["total_time_mins"]), 1
    )

    should_divert = (
        nearest["total_time_mins"] - second_nearest["total_time_mins"]
    ) > 15

    return nearest, second_nearest, time_difference, should_divert
