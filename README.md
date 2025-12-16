# EUR Currency Exchange Rate Fetcher

Airflow-based system to fetch EUR currency exchange rates from the Frankfurter API, scheduled to run weekly on Fridays at 02:00 UTC.

## Overview

This project uses Apache Airflow to orchestrate a weekly task that:
- Fetches EUR exchange rates for yesterday (T-1) from the [Frankfurter API](https://www.frankfurter.app/)
- Runs automatically every Friday at 02:00 UTC
- Saves exchange rate data to JSON files
- Runs entirely in Docker containers

## Architecture

The system consists of the following Docker services:
- **PostgreSQL**: Airflow metadata database
- **Airflow Webserver**: Web UI for monitoring and managing DAGs (port 8080)
- **Airflow Scheduler**: Executes scheduled tasks
- **Airflow Init**: Initializes the database and creates admin user

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Port 8080 available for Airflow webserver

### 1. Start the Services

```bash
```bash
# From project root
docker-compose up -d
```

This will:
- Pull the necessary Docker images
- Initialize the Airflow database
- Create an admin user (username: `airflow`, password: `airflow`)
- Start all services

### 2. Access Airflow UI

Open your browser and navigate to:
```
http://localhost:8080
```

Login credentials:
- **Username**: `airflow`
- **Password**: `airflow`

### 3. Enable the DAG

1. In the Airflow UI, you'll see the `currency_exchange_dag`
2. Toggle the switch to enable it
3. The DAG will run automatically every Friday at 02:00 UTC

### 4. Trigger Manual Run (Optional)

To test immediately without waiting for Friday:
1. Click on the `currency_exchange_dag` in the UI
2. Click the "Play" button (▶) in the top right
3. Select "Trigger DAG"
4. Monitor execution in the Grid or Graph view

## Project Structure

```
test_task/
├── dags/
│   └── currency_exchange_dag.py    # Airflow DAG definition
├── src/
│   ├── fetch_exchange_rates.py     # Currency fetcher script
│   ├── save_to_postgres.py         # Database saver script
│   └── init_currency_db.sh         # DB initialization script
├── docker-compose.yml              # Docker services configuration
├── data/                            # Exchange rate JSON files (created automatically)
├── logs/                            # Airflow logs (created automatically)
├── data/                            # Exchange rate JSON files (created automatically)
├── logs/                            # Airflow logs (created automatically)
├── requirements.txt                 # Python dependencies
└── .env                            # Environment variables
```

## Output

Exchange rate data is saved to `data/exchange_rates_YYYY-MM-DD_HHMMSS.json` with the following format:

```json
{
  "amount": 1.0,
  "base": "EUR",
  "date": "2025-12-14",
  "rates": {
    "USD": 1.0512,
    "GBP": 0.8321,
    "JPY": 159.84,
    ...
  }
}
```
