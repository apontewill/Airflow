# Project documentation

This documentation describes the repository as it exists today. It separates
the steps needed to run the learning project from recommendations that still
require code changes.

## Read in this order

1. [Getting started](getting-started.md) — prerequisites, initialization, and
   the database schema expected by the DAGs.
2. [Architecture](architecture.md) — services, data flow, and repository map.
3. [DAG catalog](dags.md) — what each DAG demonstrates and how the shared
   transformer behaves.
4. [Operations](operations.md) — configuration, endpoints, persistence, and
   local security boundaries.
5. [Troubleshooting](troubleshooting.md) — common startup and task failures.
6. [Code review](code-review.md) — prioritized findings and a remediation
   roadmap.

## Scope and current limitations

The project is a local Airflow course example:

- Airflow 3.3.0 runs with CeleryExecutor.
- Redis is the Celery broker.
- PostgreSQL stores Airflow metadata and initialized weather data.
- Every extractor requests current weather for Berlin.
- DAGs are paused when first discovered; three of the four are manual-only.

The repository has no CI workflow. Runtime verification steps and remaining
risks are recorded in the [code review](code-review.md).

## Terminology

- **Metadata database:** the `airflow` PostgreSQL database created by Compose.
- **Weather database:** the initialized `WeatherData` database used by the two
  PostgreSQL DAGs.
- **Weather record:** the transformer's one-element JSON array containing
  location, temperature, wind speed, and timestamp.
