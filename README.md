# Store Monitoring System

## Introduction

This repository contains the solution for the take-home interview assignment on Store Monitoring. The goal of this assignment is to build backend APIs that help restaurant owners monitor the online/offline status of their stores during business hours. The provided data sources include store activity logs, business hours, and timezones.

## Problem Statement

Loop monitors several restaurants in the US and needs to monitor if the store is online or not during business hours. The task is to build backend APIs that generate reports for restaurant owners, detailing how often the store went inactive in the past.

## Data Sources

1. **Store Activity Logs**: CSV containing store activity data with columns (`store_id, timestamp_utc, status`).
2. **Business Hours**: CSV with columns (`store_id, dayOfWeek(0=Monday, 6=Sunday), start_time_local, end_time_local`).
3. **Timezones for Stores**: CSV with columns (`store_id, timezone_str`).

## Data Output Schema

Generate a report with the following schema in a CSV:

```
report(
    store_id,
    uptime_last_hour(in minutes),
    uptime_last_day(in hours),
    update_last_week(in hours),
    downtime_last_hour(in minutes),
    downtime_last_day(in hours),
    downtime_last_week(in hours)
)
```

1. Uptime and downtime should only include observations within business hours.
2. Extrapolate uptime and downtime based on periodic polls to the entire time interval.

## API Endpoints

### 1. `/trigger_report` Endpoint

-   No input.
-   Output: `report_id` (random string) for polling report status.

### 2. `/get_report/{report_id}` Endpoint

-   Input: `report_id`.
-   Output:
    -   If report generation is not complete, return "Running."
    -   If report generation is complete, return "Complete" along with the CSV file with the specified schema.

## Getting Started

### Prerequisites

Make sure you have the following installed on your system:

-   [Python](https://www.python.org/) (version 3.6 or higher)
-   [Django](https://www.djangoproject.com/) (install using `pip install Django`)
-   [Django Rest Framework](https://www.django-rest-framework.org/) (install using `pip install djangorestframework`)
-   [Other dependencies as specified in requirements.txt]

### Installation and Running

1. Clone the repository:

    ```bash
    git clone https://github.com/xenitane/store-monitoring-system.git
    ```

2. Navigate to the project directory:

    ```bash
    cd Store-Monitoring-System
    ```

3. Set up your `.env` file with the following format:

    ```env
    DEBUG=False
    SECRET_KEY=""
    DATABASE_URL=sqlite:///db.sqlite3
    STORES_CSV_PATH="/path/to/your/Stores.csv"
    BUSINESS_HOURS_CSV_PATH="/path/to/your/BusinessHours.csv"
    TIMEZONES_CSV_PATH="/path/to/your/TimeZones.csv"
    ```

4. Run the setup script:

    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

5. Run the app:

    ```bash
    python manage.py runserver --noreload
    ```

The application should now be accessible at [http://localhost:8000/](http://localhost:8000/).

## Usage

### Configuration

Before running the application, make sure to configure your `.env` file with the appropriate settings. Adjust the values according to your environment.

### Triggering a Report

To trigger the generation of a new report, make a POST request to the following endpoint:

```http
POST /trigger-report/
```

Example using [curl](https://curl.se/):

```bash
curl -X POST http://localhost:8000/trigger-report/
```

### Checking Report Status

To check the status of a report and retrieve its associated CSV path, make a GET request to the following endpoint:

```http
GET /get-report/{report_id}/
```

Replace `{report_id}` with the actual ID of the report.

Example using [curl](https://curl.se/):

```bash
curl http://localhost:8000/get-report/1/
```

## Setup Script

For easier setup, you can use the provided `setup.sh` script. This script creates a virtual environment, installs project requirements, and applies database migrations.

```bash
chmod +x setup.sh
./setup.sh
```

Adjust the script as needed for your environment.

Make sure to replace `/path/to/your/` with the actual paths to your CSV files in the `.env` file. Additionally, update any other paths or configurations based on your project structure.
