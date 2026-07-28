import pendulum
from airflow.sdk import dag, task

from transformer import WeatherRecord, transform_weather_api
from weather import fetch_current_weather


@dag(
    dag_id="ETLWeatherPrint",
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["LearnDataEngineering"],
)
def etl_weather_print():
    """Fetch, transform, and print current weather using the TaskFlow API."""

    @task
    def extract() -> dict:
        return fetch_current_weather()

    @task
    def transform(weather_data: dict) -> list[WeatherRecord]:
        return transform_weather_api(weather_data)

    @task
    def load(weather_records: list[WeatherRecord]) -> None:
        print(weather_records)

    weather_data = extract()
    weather_summary = transform(weather_data)
    load(weather_summary)


etl_weather_print()
