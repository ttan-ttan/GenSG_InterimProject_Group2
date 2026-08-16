#DDL script to define the database schema.

DROP TABLE IF EXISTS hospital_wait_times;
DROP TABLE IF EXISTS weather_records;
DROP TABLE IF EXISTS dengue_clusters;

CREATE TABLE hospital_wait_times (
    id SERIAL PRIMARY KEY,
    hospital_name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,    
    postal_prefix VARCHAR(10) NOT NULL, 
    base_travel_mins INT NOT NULL,    
    wait_time_hrs NUMERIC(4, 2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weather_records (
    id SERIAL PRIMARY KEY,
    area_name VARCHAR(100) NOT NULL,
    forecast VARCHAR(100),
    is_heavy_rain BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dengue_clusters (
    id SERIAL PRIMARY KEY,
    postal_district VARCHAR(20),
    location_name VARCHAR(150),
    case_count INT DEFAULT 0,
    cluster_severity VARCHAR(50),
    report_month VARCHAR(20)
);