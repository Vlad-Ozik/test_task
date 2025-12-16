from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, '/app/src')

from fetch_exchange_rates import main as fetch_exchange_rates_main
from save_to_postgres import save_processed_data_to_db


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}


with DAG(
    dag_id='currency_exchange_dag',
    default_args=default_args,
    description='Fetch EUR exchange rates from Frankfurter API for yesterday (T-1)',
    schedule_interval='0 2 * * 5',
    catchup=False,
    tags=['currency', 'exchange-rates', 'frankfurter'],
    max_active_runs=1,
) as dag:
    
    fetch_rates_task = PythonOperator(
        task_id='fetch_eur_exchange_rates',
        python_callable=fetch_exchange_rates_main,
        dag=dag,
        execution_timeout=timedelta(minutes=10),
    )
    
    save_to_db_task = PythonOperator(
        task_id='save_to_db',
        python_callable=save_processed_data_to_db,
        op_args=[fetch_rates_task.output],
        dag=dag,
        execution_timeout=timedelta(minutes=5),
    )
    
    fetch_rates_task >> save_to_db_task


dag.doc_md = """
# Currency Exchange Rate Fetcher

This DAG fetches EUR currency exchange rates from the Frankfurter API.

## Schedule
- **Frequency**: Weekly
- **Day**: Friday
- **Time**: 02:00 UTC

## What it does
1. Calculates yesterday's date (T-1)
2. Fetches EUR exchange rates from https://api.frankfurter.app
3. Saves the data to a JSON file in `/app/data/`

## Manual Execution
You can trigger this DAG manually from the Airflow UI if needed.

## Output
Exchange rate data is saved to: `/app/data/exchange_rates_YYYY-MM-DD_HHMMSS.json`
"""
