from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from etl_weather import run_etl  # Your ETL function

# Default DAG settings
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'weather_etl_dag',
    default_args=default_args,
    description='ETL pipeline for OpenWeather data using Airflow',
    schedule_interval='@hourly',  
    start_date=datetime(2025, 4, 25),
    catchup=False,
    tags=['weather', 'etl'],
) as dag:

    # Task: Run the ETL process
    run_etl_task = PythonOperator(
        task_id='run_weather_etl',
        python_callable=run_etl
    )

    run_etl_task
