# Troubleshooting

## Compose reports a required secret is missing

Create `.env` from `.env.example`, then set non-empty values for:

- `AIRFLOW__CORE__FERNET_KEY`
- `AIRFLOW__API_AUTH__JWT_SECRET`

Generation commands are in [Getting started](getting-started.md).

## Permission denied under `/opt/airflow/logs`

Set `AIRFLOW_UID` to the host user ID and rerun initialization:

```bash
printf 'AIRFLOW_UID=%s\n' "$(id -u)" >> .env
mkdir -p logs plugins config
docker compose up airflow-init
```

## A DAG is visible but does not run

New DAGs start paused. Unpause the selected DAG in the UI. Only
`ETLWeatherPrintAirflow2` has a schedule; the other DAGs require a manual
trigger.

## DAG import fails

Inspect the dedicated Airflow 3 DAG processor:

```bash
docker compose logs airflow-dag-processor
docker compose run --rm airflow-cli dags list-import-errors
```

Confirm the image is Airflow 3.3.0 and that the standard provider is installed.

## `WEATHER_API_KEY is not configured`

Add a valid WeatherAPI key to `.env`, then recreate Airflow services so Compose
injects the new value:

```bash
docker compose up -d --force-recreate \
  airflow-apiserver airflow-scheduler airflow-dag-processor \
  airflow-worker airflow-triggerer
```

## WeatherAPI rejects the request

The extractor now fails immediately with the HTTP or API error rather than
allowing a malformed response to reach transformation. Check that the key is
active and permitted to access the current-weather endpoint.

## `database "WeatherData" does not exist`

PostgreSQL initialization scripts run only on an empty volume. For disposable
local data, recreate the volume:

```bash
docker compose down --volumes --remove-orphans
docker compose up airflow-init
```

Do not use that command when the volume contains data you need.

## Duplicate weather readings

The table primary key is `(location, time)`, and loaders use
`ON CONFLICT DO UPDATE`. A retry updates temperature and wind values for the
same reading rather than creating a duplicate.

## API server is not reachable remotely

Port 8080 intentionally binds to `127.0.0.1`. Use local access or an
authenticated TLS reverse proxy. Do not change it to an all-interface binding
on an untrusted machine.

## Migrating an existing Airflow 2 metadata database

This project's quick-start expects a new disposable PostgreSQL volume. A real
Airflow 2 installation must first be upgraded to at least Airflow 2.7
(preferably the latest 2.x), backed up, checked for removed features, and then
migrated with `airflow db migrate`. Follow the
[official Airflow 3 upgrade guide](https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html).
