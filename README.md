# Airflow weather ETL

An educational Apache Airflow project that fetches current weather for Berlin,
reduces the response to a few useful fields, and prints or stores the result in
PostgreSQL. Four DAGs show the progression from a classic `PythonOperator`
pipeline to TaskFlow pipelines with multiple load targets.

> [!WARNING]
> This repository is a learning example, not a production deployment. The
> Compose stack still uses local default database credentials and is not
> production hardened. Configure unique secrets in `.env` and review the
> [code review](docs/code-review.md) before exposing any service.

## Documentation

- [Documentation home](docs/README.md)
- [Getting started](docs/getting-started.md)
- [Architecture and data flow](docs/architecture.md)
- [DAG catalog and code guide](docs/dags.md)
- [Configuration and operations](docs/operations.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Code review and recommended improvements](docs/code-review.md)

## Pipeline at a glance

```text
WeatherAPI
    |
    v
 extract --> transform --> print to task log
                         \-> insert into PostgreSQL
```

The shared transformer produces records with `location`, `temp_c`, `wind_kph`,
and a timezone-aware `timestamp`. PostgreSQL initialization creates the
separate `WeatherData` database and its `temperature` table.

## Local services

The Compose file starts Airflow 3.3.0 with CeleryExecutor, PostgreSQL, and Redis.
Flower is available through an optional profile:

| Service | URL |
| --- | --- |
| Airflow API server and UI | <http://localhost:8080> |
| Flower (optional) | <http://localhost:5555> |

Start with the [getting-started guide](docs/getting-started.md). The project is
pinned to the current stable Airflow 3.3.0 image for reproducible local runs.
