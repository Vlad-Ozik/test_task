from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.sensors.http import HttpSensor
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
    'start_date': days_ago(10),
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
    
    start_task = HttpSensor(
        task_id='start',
        http_conn_id='frankfurter_api',
        endpoint='',
        request_params=None,
        response_check=lambda response: response.status_code == 200,
        poke_interval=20,
        timeout=60,
        dag=dag,
    )

    fetch_rates_task = PythonOperator(
        task_id='fetch_eur_exchange_rates',
        python_callable=fetch_exchange_rates_main,
        op_kwargs={'execution_date': '{{ ds }}'},
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
    
    start_task >> fetch_rates_task >> save_to_db_task


dag.doc_md = """
# Currency Exchange Rate Fetcher

This DAG fetches EUR currency exchange rates from the Frankfurter API.

## Schedule
- **Frequency**: Weekly
- **Day**: Friday
- **Time**: 02:00 UTC

## What it does
1. Determines the Reference Friday (Execution Date if Friday, else previous Friday)
2. Fetches EUR exchange rates for T-1 (Thursday) and T-2 (Wednesday) relative to Reference Friday
3. Calculates % change
4. Saves the data to a JSON file in `/app/data/`2. Fetches EUR exchange rates from https://api.frankfurter.app
3. Saves the data to a JSON file in `/app/data/`

## Manual Execution
You can trigger this DAG manually from the Airflow UI if needed.

## Output
Exchange rate data is saved to: `/app/data/exchange_rates_YYYY-MM-DD_HHMMSS.json`
"""
