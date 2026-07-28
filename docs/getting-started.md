# Getting started

## Prerequisites

- Docker Engine with Docker Compose 2.14 or newer
- At least 4 GB RAM, 2 CPUs, and 10 GB free disk
- A WeatherAPI account and API key
- Port 8080 available on the local machine

The stack is pinned to `apache/airflow:3.3.0`, the current stable Airflow
release when this guide was updated.

## 1. Create local configuration

Copy the example file:

```bash
cp .env.example .env
```

Set the host UID on Linux:

```bash
printf 'AIRFLOW_UID=%s\n' "$(id -u)" >> .env
```

Generate a Fernet key:

```bash
docker run --rm apache/airflow:3.3.0 \
  python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Generate an API JWT secret:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Place those values in `AIRFLOW__CORE__FERNET_KEY` and
`AIRFLOW__API_AUTH__JWT_SECRET` in `.env`. Add the WeatherAPI credential as
`WEATHER_API_KEY`. The file is ignored by Git; never commit it.

Create the bind-mounted directories:

```bash
mkdir -p logs plugins config
```

## 2. Initialize and start Airflow

Initialize the metadata and weather databases and create the local Airflow
administrator:

```bash
docker compose up airflow-init
```

After the initializer exits successfully, start the stack:

```bash
docker compose up -d
docker compose ps
```

Airflow is available only on the host loopback interface at
<http://localhost:8080>. Unless overridden in `.env`, the quick-start login is
`airflow` / `airflow`.

The stack starts:

- API server and UI
- scheduler
- DAG processor
- Celery worker
- triggerer
- PostgreSQL 16
- Redis 7.2

Flower is optional:

```bash
docker compose --profile flower up -d flower
```

## 3. Run a DAG

In the Airflow UI:

1. Find DAGs tagged `LearnDataEngineering`.
2. Unpause the DAG you want to use.
3. Trigger it manually, except for `ETLWeatherPrintAirflow2`, which is scheduled
   hourly after it is unpaused.
4. Open task logs to inspect the transformed output or insert result.

Start with `ETLWeatherPrint`. The two PostgreSQL DAGs use the `WeatherData`
database and `temperature` table created automatically by
`docker/postgres-init/01-weather-database.sql`.

## Stop and clean up

Stop containers while retaining database data:

```bash
docker compose down
```

Delete all local database data and recreate a clean environment:

```bash
docker compose down --volumes --remove-orphans
```

The second command is destructive.
