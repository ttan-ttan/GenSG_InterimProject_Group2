#DDL script to define the database schema.

DROP TABLE IF EXISTS hospital_wait_times;

DROP TABLE IF EXISTS weather_history;

DROP TABLE IF EXISTS weather_realtime;

DROP TABLE IF EXISTS weather_forecast;

DROP TABLE IF EXISTS dengue_clusters;

CREATE TABLE hospital_wait_times (
    id SERIAL PRIMARY KEY,
    hospital_name VARCHAR(100) NOT NULL,
    patients_waiting_count INT,
    doctor_wait_minutes INT,
    wait_time_hrs NUMERIC(4, 2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weather_realtime (
    id SERIAL PRIMARY KEY,
    area_name VARCHAR(100) NOT NULL UNIQUE,
    reading_value DECIMAL(5, 2) NOT NULL DEFAULT 0.0,
    is_heavy_rain BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weather_forecast (
    id SERIAL PRIMARY KEY,
    area_name VARCHAR(100) NOT NULL UNIQUE,
    forecast_text VARCHAR(100) NOT NULL,
    will_rain BOOLEAN NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weather_history (
    id SERIAL PRIMARY KEY,
    record_date DATE NOT NULL UNIQUE,
    total_rainfall_mm NUMERIC(5, 2) NOT NULL,
    is_catalyst_day BOOLEAN DEFAULT FALSE
);

CREATE TABLE dengue_clusters (
    id SERIAL PRIMARY KEY,
    postal_district VARCHAR(20),
    location_name VARCHAR(150),
    case_count INT DEFAULT 0,
    cluster_severity VARCHAR(50),
    report_month VARCHAR(20)
);