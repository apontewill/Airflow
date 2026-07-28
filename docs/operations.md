# Configuration and operations

## Compose services

| Service | Purpose | Host access |
| --- | --- | --- |
| `postgres` | Airflow metadata and weather databases | Internal only |
| `redis` | Celery broker | Internal only |
| `airflow-apiserver` | Airflow 3 UI, REST, and execution APIs | `127.0.0.1:8080` |
| `airflow-scheduler` | DAG scheduling | Internal only |
| `airflow-dag-processor` | DAG parsing and serialization | Internal only |
| `airflow-worker` | Task execution | Internal only |
| `airflow-triggerer` | Deferred task handling | Internal only |
| `airflow-init` | Database migration and local user creation | One-shot |
| `airflow-cli` | Debug profile | On demand |
| `flower` | Optional Celery monitoring | `127.0.0.1:5555` |

## Configuration

Compose reads `.env` automatically. Important variables are:

| Variable | Default | Purpose |
| --- | --- | --- |
| `AIRFLOW_IMAGE_NAME` | `apache/airflow:3.3.0` | Airflow image |
| `AIRFLOW_UID` | `50000` | UID used by Airflow containers |
| `AIRFLOW__CORE__FERNET_KEY` | required | Encrypts stored Airflow secrets |
| `AIRFLOW__API_AUTH__JWT_SECRET` | required | Signs execution API tokens |
| `WEATHER_API_KEY` | empty | WeatherAPI credential used by extract tasks |
| `_AIRFLOW_WWW_USER_USERNAME` | `airflow` | Initial local administrator |
| `_AIRFLOW_WWW_USER_PASSWORD` | `airflow` | Initial local password |

The repository no longer installs packages at container startup. Airflow 3.3's
reference image supplies the standard, Celery, PostgreSQL, FAB, Requests, and
psycopg2 dependencies used by the DAGs. The weather transformation uses only
the Python standard library.

## Persistence

- `postgres-db-volume` stores both PostgreSQL databases.
- `./logs` stores Airflow logs.
- `./dags`, `./config`, and `./plugins` are mounted into Airflow containers.
- `docker/postgres-init` is mounted read-only during first-time PostgreSQL
  initialization.

Initialization scripts run only when the PostgreSQL volume is empty. To apply a
changed initialization script to disposable local data, remove the volume and
initialize again.

## Health and diagnostics

```bash
docker compose ps
docker compose logs airflow-init
docker compose logs airflow-apiserver
docker compose logs airflow-scheduler
docker compose logs airflow-dag-processor
docker compose logs airflow-worker
```

The API health endpoint is:

```bash
curl --fail http://127.0.0.1:8080/api/v2/monitor/health
```

## Local security model

This remains a learning stack:

- PostgreSQL uses a known internal password.
- The default UI credentials are predictable unless overridden.
- secrets are stored in a local `.env`.
- TLS is not configured.

Published ports bind only to loopback, examples are disabled, mutable
management surfaces were removed, application credentials are no longer
committed, API traffic uses HTTPS, and Fernet/JWT secrets are required.

Do not expose this Compose stack directly to a network. Production deployment
needs external secret management, TLS ingress, unique database credentials,
backups, observability, and a supported deployment architecture such as the
official Airflow Helm chart.

## Version policy

The deployment pins:

- Apache Airflow 3.3.0
- PostgreSQL 16
- Redis 7.2 Bookworm

Review and test minor upgrades before changing these tags. Database upgrades
must be backed up and run through `airflow db migrate`; do not downgrade a
migrated metadata database.
