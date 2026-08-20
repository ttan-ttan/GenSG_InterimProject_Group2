# Hospital A&E: Factors Contributing to Waiting Time

## Project Overview
This project, developed by a group of four learners from the Generation SG Junior Data Engineering Bootcamp at Temasek Polytechnic, aims to optimize patient routing to Accident & Emergency (A&E) departments.

In emergency situations, patients often choose the closest hospital. However, if the nearest facility is experiencing a surge in patients, a further hospital with a shorter wait time may be a better option. This project implements "Total Time-to-Treatment" logic to recommend the optimal A&E department, considering factors such as:
* Live A&E queue data
* Real-time weather conditions
* Proximity to active dengue clusters

## Team Member

<div align="center">
  <table>
    <tr>
      <td align="center">1) Ana N<br><img src="https://placeholder.com+" height="1" width="180" /></td>
      <td align="center">2) Jie Song L<br><img src="https://placeholder.com+" height="1" width="180" /></td>
      <td align="center">3) Jun Jie Y<br><img src="https://placeholder.com+" height="1" width="180" /></td>
      <td align="center">4) Yong Jian T<br><img src="https://placeholder.com+" height="1" width="180" /></td>
    </tr>
  </table>
</div>

<p align="center">
  <img width="767" height="88" alt="image" src="https://github.com/user-attachments/assets/168f2ad2-988e-431f-850a-7bf114f14e12" />
</p>

## Technical Stack
* **Language:** Python
* **Database:** PostgreSQL
* **Development Environment:** Visual Studio Code
* **Collaboration:** GitHub, Google Drive

## Project Structure
The project repository follows this structure:

GenSG_InterimProject_Group2/<br />
├── data/<br />
│   ├── archive/<br />
│   ├── processed/<br />
│   └── raw/<br />
├── doc/<br />
│   ├── database_schema.sql<br />
│   ├── database_schema.png<br />
│   └── presentation_deck.pptx<br />
├── notebooks/<br />
│   └── exploratory_analysis.ipynb<br />
├── src/<br />
│   ├── extractors/<br />
│   ├── load/<br />
│   ├── transform/<br />
│   ├── __init__.py<br />
│   ├── geocode.py<br />
│   ├── main.py<br />
│   ├── routing_logic.py<br />
│   └── visualization.py<br />
├── test/<br />
│   ├── test_extract.py<br />
│   ├── test_loader.py<br />
│   ├── test_transform_data.py<br />
│   └── test_transform.py<br />
├── .env.example<br />
├── .gitignore<br />
├── README.md<br />
└── requirements.txt<br />

## Database Schema
The system utilizes five PostgreSQL tables:
1. **hospital_wait_times:** Tracks current patient counts and wait durations.
2. **weather_realtime:** Monitors current area-based weather and rainfall status.
3. **weather_forecast:** Stores predicted weather conditions by area.
4. **weather_history:** Archives daily rainfall data to identify environmental catalysts.
5. **dengue_clusters:** Logs case counts, severity, and reporting periods for dengue clusters.

## Project Outcomes & Analytics
* **Dengue Clusters:** Identification of high-risk districts (e.g., D78) allows for prioritized public health interventions.
* **Weather Trends:** Analysis of rainfall patterns provides insights into potential future surges in mosquito-borne illnesses.
* **A&E Routing:** Real-time analysis of hospital wait times allows for dynamic patient redirection from congested facilities (e.g., SKH, KTPH) to those with lower wait times (e.g., TTSH).
* **Integrated Dashboards:** Synthesis of environmental and epidemiological data provides a comprehensive risk overview.

## Getting Started
Ensure you have the required packages installed as listed in the `requirements.txt` file within the repository.

## Acknowledgments
* Generation SG
* Temasek Polytechnic
* Microsoft
* Instructor Christine
