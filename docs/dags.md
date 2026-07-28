# DAG catalog and code guide

All four DAGs are tagged `LearnDataEngineering`. The Compose configuration
pauses newly discovered DAGs, so each must be enabled in the UI before its
schedule or a manual trigger can run.

## DAG comparison

| DAG ID | Source | API style | Schedule | Output |
| --- | --- | --- | --- | --- |
| `ETLWeatherPrintAirflow2` | `00_ETLWeatherPrintAirflow2.py` | `PythonOperator` and explicit XCom | Hourly | Airflow task log |
| `ETLWeatherPrint` | `01-ETLWeatherPrint.py` | TaskFlow | Manual | Printed task log |
| `ETLWeatherPostgres` | `02-ETLWeatherPostgres.py` | TaskFlow | Manual | PostgreSQL row |
| `ETLWeatherPostgresAndPrint` | `03-ETLWeatherPostgresAndPrint.py` | TaskFlow | Manual | PostgreSQL row and printed task log |

## `ETLWeatherPrintAirflow2`

This is the legacy-style example:

```text
extract -> transform -> load
```

- `my_extract` requests the API, serializes the object, and pushes
  `api_result`.
- `my_transform` pulls `api_result`, invokes the shared transformer, and pushes
  `transformed_weather`.
- `my_load` pulls that value and logs it through the `airflow.task` logger.

It demonstrates explicit XComs, but uses the deprecated
`airflow.operators.python_operator` import and redundant `provide_context=True`
arguments. Those should not be copied into new Airflow code.

## `ETLWeatherPrint`

This is the smallest TaskFlow example:

```text
extract -> transform -> load
```

Task dependencies are inferred from returned values passed as task arguments.
Although `load` is annotated with `dict`, the actual transformed value is a
list of dictionaries.

## `ETLWeatherPostgres`

This extends the TaskFlow example with a direct PostgreSQL insert:

```text
extract -> transform -> load -> WeatherData.temperature
```

The loader:

- assumes the transform output contains at least one item;
- inserts only item `0`;
- uses hardcoded connection details rather than an Airflow Connection;
- commits one row per run; and
- uses a plain `INSERT`, so retries and reruns are not idempotent.

If connection creation fails, the exception handler references `connection`
before it has necessarily been assigned. This can replace the useful database
error with `UnboundLocalError`.

## `ETLWeatherPostgresAndPrint`

This example fans out after transformation:

```text
                    +-> load -> WeatherData.temperature
extract -> transform
                    +-> query_print -> task log
```

`load` and `query_print` are independent downstream tasks and may run in
parallel. Despite its name, `query_print` does not query PostgreSQL; it prints
the in-memory transformed record. The `load` docstring is also inaccurate: the
task does save to PostgreSQL.

## Shared transformer

`transform_weatherAPI(im_json)` accepts a JSON string and returns a JSON string
containing an array of records.

| Input field | Output field | Notes |
| --- | --- | --- |
| `location.name` | `location` | City name |
| `current.temp_c` | `temp_c` | Celsius |
| `current.wind_kph` | `wind_kph` | Kilometres per hour |
| `location.localtime_epoch` | `timestamp` | Currently formatted with a fixed offset |

The transformer also renames `location.region` to `region`, then filters it out.
It prints the complete input response, which can create noisy logs. Pandas is
substantial for this four-field transform; normal dictionary access would
reduce startup and dependency overhead.

## Scheduling semantics

- `ETLWeatherPrintAirflow2` uses cron `0 * * * *` and `catchup=False`.
- The TaskFlow DAGs use `schedule_interval=None` and are manual-only.
- All start dates are historical and therefore already eligible to run.
- Airflow 3 removed `schedule_interval`; migrating requires `schedule=...` and
  additional API/import changes described in the [code review](code-review.md).
