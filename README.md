# Airflow weather ETL

An educational Apache Airflow project that fetches current weather for Berlin,
reduces the response to a few useful fields, and prints or stores the result in
PostgreSQL. Four DAGs show the progression from a classic `PythonOperator`
pipeline to TaskFlow pipelines with multiple load targets.

> [!WARNING]
> This repository is a learning example, not a production deployment. The
> current code contains an exposed WeatherAPI key, default local credentials,
> an empty Fernet key, and an unsupported Airflow version. Rotate the exposed
> API key before using the project and review the
> [code review](docs/code-review.md).

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
and `timestamp`. The PostgreSQL DAGs expect a separate `WeatherData` database
and a `temperature` table; the Compose stack does not currently create either.

## Local services

The Compose file starts Airflow with CeleryExecutor plus PostgreSQL, Redis,
Flower, Adminer, and Portainer. Its default web endpoints are:

| Service | URL |
| --- | --- |
| Airflow | <http://localhost:8080> |
| Adminer | <http://localhost:8081> |
| Flower | <http://localhost:5555> |
| Portainer | <http://localhost:9000> |

Start with the [getting-started guide](docs/getting-started.md). Do not install
the latest Airflow package with an unconstrained `pip install`: this project is
pinned to Airflow 2.2.4 and is not compatible with Airflow 3 without migration.
