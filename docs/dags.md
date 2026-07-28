# DAG catalog and code guide

All DAGs use Airflow 3's public `airflow.sdk` authoring API and are tagged
`LearnDataEngineering`. New DAGs start paused.

## DAG comparison

| DAG ID | Source | API style | Schedule | Output |
| --- | --- | --- | --- | --- |
| `ETLWeatherPrintAirflow2` | `00_ETLWeatherPrintAirflow2.py` | Standard provider `PythonOperator` and explicit XCom | Hourly | Task log |
| `ETLWeatherPrint` | `01-ETLWeatherPrint.py` | TaskFlow | Manual | Task log |
| `ETLWeatherPostgres` | `02-ETLWeatherPostgres.py` | TaskFlow | Manual | PostgreSQL upsert |
| `ETLWeatherPostgresAndPrint` | `03-ETLWeatherPostgresAndPrint.py` | TaskFlow | Manual | PostgreSQL and task log |

## `ETLWeatherPrintAirflow2`

```text
extract -> transform -> load
```

This preserves the project's classic-operator lesson while using supported
Airflow 3 imports:

- `DAG` comes from `airflow.sdk`.
- `PythonOperator` comes from `airflow.providers.standard`.
- runtime context is provided automatically.
- `schedule` replaces the removed `schedule_interval`.

The tasks explicitly push and pull named XCom values.

## `ETLWeatherPrint`

```text
extract -> transform -> load
```

This is the smallest TaskFlow example. Dependencies are inferred from task
return values passed as arguments. The load task prints
`list[WeatherRecord]` to its task log.

## `ETLWeatherPostgres`

```text
extract -> transform -> load -> WeatherData.temperature
```

The load task checks that at least one record exists and upserts item `0`.
The database helper uses environment-based connection settings, a ten-second
connection timeout, context-managed cleanup, and a conflict key of
`(location, time)`.

## `ETLWeatherPostgresAndPrint`

```text
                    +-> load -> WeatherData.temperature
extract -> transform
                    +-> print_weather -> task log
```

The two downstream tasks are independent and may run in parallel.

## Shared modules

### `weather.py`

- `fetch_current_weather` retrieves and validates Berlin weather over HTTPS.
- `store_weather_record` idempotently writes one record to PostgreSQL.
- configuration comes from environment variables supplied by Compose.

### `transformer.py`

`transform_weather_api` produces:

| Input field | Output field | Notes |
| --- | --- | --- |
| `location.name` | `location` | City name |
| `current.temp_c` | `temp_c` | Celsius |
| `current.wind_kph` | `wind_kph` | Kilometres per hour |
| `location.localtime_epoch` and `location.tz_id` | `timestamp` | Timezone-aware ISO 8601 |

It uses standard-library JSON, datetime, and zoneinfo modules; Pandas is no
longer required.

## Scheduling semantics

- `ETLWeatherPrintAirflow2` uses `schedule="0 * * * *"` and `catchup=False`.
- TaskFlow DAGs use `schedule=None` and are manual-only.
- all start dates are timezone-aware.
- stable DAG IDs are set explicitly so migration does not rename existing DAGs.
