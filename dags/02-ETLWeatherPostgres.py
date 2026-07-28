import pendulum
from airflow.sdk import dag, task

from transformer import WeatherRecord, transform_weather_api
from weather import fetch_current_weather, store_weather_record


@dag(
    dag_id="ETLWeatherPostgres",
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["LearnDataEngineering"],
)
def etl_weather_postgres():
    """Fetch current weather and persist one normalized record."""

    @task
    def extract() -> dict:
        return fetch_current_weather()

    @task
    def transform(weather_data: dict) -> list[WeatherRecord]:
        return transform_weather_api(weather_data)

    @task
    def load(weather_records: list[WeatherRecord]) -> None:
        if not weather_records:
            raise ValueError("The transformer returned no weather records")
        store_weather_record(weather_records[0])

    weather_data = extract()
    weather_summary = transform(weather_data)
    load(weather_summary)


etl_weather_postgres()
