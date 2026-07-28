# Getting started

## Prerequisites

- Docker Engine with Docker Compose
- At least 4 GB RAM, 2 CPUs, and 10 GB free disk
- A WeatherAPI account and a newly issued API key
- Ports 8080, 8081, 5555, 9000, and 8000 available locally

The repository targets `apache/airflow:2.2.4`. It is not a guide for installing
Airflow directly in WSL or with an unconstrained `pip install apache-airflow`.

## 1. Configure the host user

On Linux, create a local `.env` before starting the stack:

```bash
printf 'AIRFLOW_UID=%s\n' "$(id -u)" > .env
mkdir -p logs plugins
```

This prevents the root-owned log directory problem that can stop Airflow from
writing scheduler and task logs. Do not commit `.env`.

## 2. Configure the Weather API key

The extractors currently contain the same committed key in each DAG. Treat
that key as compromised and rotate it.

There is not yet a safe configuration interface in this repository. Before
running a DAG, replace the hardcoded value only in a private working copy.
The preferred code improvement is to use an Airflow Connection or secrets
backend and HTTPS; see the [code review](code-review.md#p0-security-and-access).
Never commit the replacement key.

## 3. Initialize and start Airflow

Initialize the Airflow database and administrator account:

```bash
docker compose up airflow-init
```

After the initialization container exits successfully, start the services:

```bash
docker compose up -d
docker compose ps
```

Airflow is available at <http://localhost:8080>. Unless overridden in `.env`,
the local example creates an `airflow` user with password `airflow`.

## 4. Prepare the weather database

Compose creates the `airflow` metadata database, but the PostgreSQL DAGs connect
to a different database named `WeatherData`. Create it:

```bash
docker compose exec postgres createdb -U airflow WeatherData
```

Then create the table expected by the loaders:

```bash
docker compose exec -T postgres psql -U airflow -d WeatherData <<'SQL'
CREATE TABLE IF NOT EXISTS temperature (
    location TEXT NOT NULL,
    temp_c DOUBLE PRECISION NOT NULL,
    wind_kph DOUBLE PRECISION NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    UNIQUE (location, time)
);
SQL
```

This is a **recommended schema inferred from the INSERT statement**, not a
versioned schema supplied by the application. The unique constraint helps
prevent duplicate readings, but the current plain `INSERT` will fail rather
than update when the same reading is loaded twice.

## 5. Run a DAG

In the Airflow UI:

1. Find DAGs tagged `LearnDataEngineering`.
2. Unpause the DAG you want to use.
3. Trigger it manually, except for `ETLWeatherPrintAirflow2`, which is scheduled
   hourly after it is unpaused.
4. Open the task logs to inspect the transformed output or insert result.

Start with `ETLWeatherPrint`; it does not require the weather database.

## Stop and clean up

Stop containers while keeping database volumes:

```bash
docker compose down
```

To also delete PostgreSQL and Portainer data:

```bash
docker compose down --volumes
```

The second command is destructive.
