import logging

import pendulum
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

from transformer import transform_weather_api
from weather import fetch_current_weather


def my_extract(**context):
    weather_data = fetch_current_weather()
    context["ti"].xcom_push(key="api_result", value=weather_data)
    return weather_data


def my_transform(**context):
    task_instance = context["ti"]
    api_data = task_instance.xcom_pull(key="api_result", task_ids="extract")
    weather_records = transform_weather_api(api_data)
    task_instance.xcom_push(key="transformed_weather", value=weather_records)


def my_load(**context):
    task_instance = context["ti"]
    weather_records = task_instance.xcom_pull(
        key="transformed_weather", task_ids="transform"
    )
    logger = logging.getLogger("airflow.task")
    logger.info("Transformed weather records: %s", weather_records)


with DAG(
    dag_id="ETLWeatherPrintAirflow2",
    description="Classic PythonOperator weather ETL example",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    schedule="0 * * * *",
    catchup=False,
    tags=["LearnDataEngineering"],
) as dag:
    ext = PythonOperator(
        task_id="extract",
        python_callable=my_extract,
    )

    trn = PythonOperator(
        task_id="transform",
        python_callable=my_transform,
    )

    lds = PythonOperator(
        task_id="load",
        python_callable=my_load,
    )

    ext >> trn >> lds
