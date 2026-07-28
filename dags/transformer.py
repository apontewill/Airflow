import json
from datetime import datetime, timezone
from typing import Any, Mapping, TypedDict, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class WeatherRecord(TypedDict):
    location: str
    temp_c: float
    wind_kph: float
    timestamp: str


def transform_weather_api(
    weather_data: Union[str, Mapping[str, Any]],
) -> list[WeatherRecord]:
    """Reduce a WeatherAPI response to the fields persisted by this project."""
    api_json = json.loads(weather_data) if isinstance(weather_data, str) else weather_data

    try:
        location = api_json["location"]
        current = api_json["current"]
        timezone_name = location["tz_id"]
        localtime_epoch = location["localtime_epoch"]
    except (KeyError, TypeError) as error:
        api_error = api_json.get("error") if isinstance(api_json, Mapping) else None
        if api_error:
            raise ValueError(f"WeatherAPI returned an error: {api_error}") from error
        raise ValueError("WeatherAPI response is missing required weather fields") from error

    try:
        location_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"Unknown WeatherAPI timezone: {timezone_name}") from error

    timestamp = (
        datetime.fromtimestamp(localtime_epoch, tz=timezone.utc)
        .astimezone(location_timezone)
        .isoformat()
    )

    return [
        {
            "location": location["name"],
            "temp_c": float(current["temp_c"]),
            "wind_kph": float(current["wind_kph"]),
            "timestamp": timestamp,
        }
    ]
