"""Extractor for live NUSH TTSH web scraping and mocking missing hospital"""

from datetime import datetime
import json
from pathlib import Path
import random
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# save the extracted data into data/raw for future use


def save_raw_hospital_data(rraw_records):
    output_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "hospital_wait_times.json"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(rraw_records, f, ensure_ascii=False,
                      indent=4, default=str)
        print(
            f"OOO Successfully saved {len(rraw_records)} hospital records to {output_file}.")
    except Exception as e:
        print(f"XXX Error saving hospital data to JSON: {e}")

# scrapper function for AH,NUH, NTFGH from NUH website
# use css selector to search table.datatable, find column header hospital and patient


def scrape_nuhs_wait_times():
    url = "https://www.nuhs.edu.sg/patient-care/emergency-department-wait-times"
    hospitals_data = []

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run browser in background
    # prevent linux server target closed error
    options.add_argument("--no-sandbox")
    # prevent linix to use ram memory
    options.add_argument("--disable-dev-shm-usage")

    # pylint: disable=not-callable
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        table = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table.dataTable"))
        )

        rows = table.find_elements(By.TAG_NAME, "tr")

        header_cells = rows[0].find_elements(By.TAG_NAME, "th")
        if not header_cells:
            header_cells = rows[0].find_elements(By.TAG_NAME, "td")
        hospitals = [cell.text.strip() for cell in header_cells[1:]]

        parsed_results = {
            h: {"patients_waiting": None, "doctor_wait": None}
            for h in hospitals
            if h
        }

        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 2:
                continue
            metric_label = cols[0].text.strip()

            for idx, col in enumerate(cols[1:]):
                if idx < len(hospitals):
                    h_name = hospitals[idx]
                    val = col.text.strip()

                    if "Patients Waiting" in metric_label:
                        parsed_results[h_name]["patients_waiting"] = val
                    elif "Time to See Doctor" in metric_label:
                        parsed_results[h_name]["doctor_wait"] = val

        timestamp = datetime.now()
        for h_name, metrics in parsed_results.items():
            if h_name:
                hospitals_data.append(
                    {
                        "hospital_name": h_name,
                        "patients_waiting": metrics["patients_waiting"],
                        "doctor_wait_time": metrics["doctor_wait"],
                        "updated_at": timestamp,
                    }
                )
    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(f"XXX Error scraping NUHS portal: {e}")
    finally:
        driver.quit()

    return hospitals_data

# scrap TTSH data using primary card div and pull data using re.findall


def scrape_ttsh_wait_time():
    url = "https://www.nhghealth.com.sg/ttsh/patients-visitors/emergency-medicine"
    ttsh_record = None

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # pylint: disable=not-callable
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.s-edq-primary-card"))
        )

        cards = driver.find_elements(By.CSS_SELECTOR, "div.s-edq-primary-card")

        patients_waiting = "N/A"
        doctor_wait = "N/A"

        for card in cards:
            card_text = card.text.strip()

            if "Patient" in card_text:
                numbers = re.findall(r'\d+', card_text)
                if numbers:
                    patients_waiting = f"{numbers[0]} patient(s)"
            elif "min" in card_text or "Hour" in card_text or "Hours" in card_text:
                numbers = re.findall(r'\d+', card_text)
                if numbers:
                    doctor_wait = f"{numbers[0]} min"

        ttsh_record = {
            "hospital_name": "Tan Tock Seng Hospital (TTSH)",
            "patients_waiting": patients_waiting,
            "doctor_wait_time": doctor_wait,
            "updated_at": datetime.now(),
        }
    # pylint: disable=broad-exception-caught
    except Exception as e:
        print(f"XXX Error scraping TTSH portal: {e}")
    finally:
        driver.quit()

    return ttsh_record

# mock missing hospital by stimulate 10am-8pm as peak(ran 20-55) others as low(10-25)


def generate_mock_hospitals():
    """Generates realistic mock records for missing hospitals:
    SGH, SKH, CGH, KTPH.
    """
    missing_hospitals = [
        "Singapore General Hospital (SGH)",
        "Sengkang General Hospital (SKH)",
        "Changi General Hospital (CGH)",
        "Khoo Teck Puat Hospital (KTPH)",
    ]

    mock_records = []
    timestamp = datetime.now()
    hour = timestamp.hour

    for h in missing_hospitals:
        base_patients = random.randint(
            20, 55) if 10 <= hour <= 20 else random.randint(10, 25)
        base_doc_wait = f"{random.randint(1, 3)} hour(s)"

        mock_records.append(
            {
                "hospital_name": h,
                "patients_waiting": f"{base_patients} patient(s)",
                "doctor_wait_time": base_doc_wait,
                "updated_at": timestamp,
            }
        )

    return mock_records

# combining all the scrap and mock


def fetch_all_hospital_data():
    print("Fetching live NUHS data...")
    nuhs_data = scrape_nuhs_wait_times()

    print("Fetching live TTSH data...")
    ttsh_data = scrape_ttsh_wait_time()

    print("Generating simulated data for remaining cluster hospitals...")
    mock_data = generate_mock_hospitals()

    combined_data = nuhs_data + mock_data
    if ttsh_data:
        combined_data.append(ttsh_data)

    if combined_data:
        save_raw_hospital_data(combined_data)

    return combined_data


if __name__ == "__main__":
    results = fetch_all_hospital_data()
    for r in results:
        print(r)
