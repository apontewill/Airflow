import os
from typing import Any

import psycopg2
import requests

from transformer import WeatherRecord


WEATHER_API_URL = "https://api.weatherapi.com/v1/current.json"


def fetch_current_weather(city: str = "Berlin") -> dict[str, Any]:
    """Fetch and validate current weather data for a city."""
    api_key = os.environ.get("WEATHER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "WEATHER_API_KEY is not configured. Add it to the Airflow environment."
        )

    response = requests.get(
        WEATHER_API_URL,
        params={"key": api_key, "q": city, "aqi": "no"},
        timeout=(5, 30),
    )
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"WeatherAPI returned an error: {payload['error']}")
    if "location" not in payload or "current" not in payload:
        raise RuntimeError("WeatherAPI response does not contain current weather data")

    return payload


def store_weather_record(record: WeatherRecord) -> None:
    """Upsert one weather record into the project database."""
    connection_options = {
        "user": os.environ.get("WEATHER_DB_USER", "airflow"),
        "password": os.environ.get("WEATHER_DB_PASSWORD", "airflow"),
        "host": os.environ.get("WEATHER_DB_HOST", "postgres"),
        "port": os.environ.get("WEATHER_DB_PORT", "5432"),
        "dbname": os.environ.get("WEATHER_DB_NAME", "WeatherData"),
        "connect_timeout": 10,
    }
    query = """
        INSERT INTO temperature (location, temp_c, wind_kph, time)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (location, time)
        DO UPDATE SET temp_c = EXCLUDED.temp_c, wind_kph = EXCLUDED.wind_kph
    """
    values = (
        record["location"],
        record["temp_c"],
        record["wind_kph"],
        record["timestamp"],
    )

    with psycopg2.connect(**connection_options) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
