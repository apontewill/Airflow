# Configuration and operations

## Compose services

| Service | Purpose | Host access |
| --- | --- | --- |
| `postgres` | Airflow metadata and weather databases | Internal only |
| `redis` | Celery broker | Internal only |
| `airflow-webserver` | Airflow UI and API | Port 8080 |
| `airflow-scheduler` | DAG scheduling | Internal only |
| `airflow-worker` | Task execution | Internal only |
| `airflow-triggerer` | Deferred task handling | Internal only |
| `airflow-init` | Database upgrade and initial user creation | One-shot |
| `airflow-cli` | Debug profile | On demand |
| `flower` | Celery monitoring | Port 5555 |
| `adminer` | Database UI | Port 8081 |
| `portainer` | Docker management UI | Ports 9000 and 8000 |

## Supported environment overrides

The Compose file recognizes:

| Variable | Default | Purpose |
| --- | --- | --- |
| `AIRFLOW_IMAGE_NAME` | `apache/airflow:2.2.4` | Airflow container image |
| `AIRFLOW_UID` | `50000` | UID used by Airflow containers |
| `_AIRFLOW_WWW_USER_USERNAME` | `airflow` | Initial local administrator |
| `_AIRFLOW_WWW_USER_PASSWORD` | `airflow` | Initial local password |
| `_PIP_ADDITIONAL_REQUIREMENTS` | empty | Packages installed at container startup |

Installing dependencies at every container startup is useful only for
experiments. A custom, versioned image and lock/constraints file is the
reproducible approach.

The Python code imports Airflow, Pendulum, Requests, Pandas, and psycopg2. The
repository does not declare or lock these dependencies independently of the
Airflow image.

## Persistence

- `postgres-db-volume` stores PostgreSQL data.
- `portainer_data` stores Portainer configuration.
- `./logs` stores Airflow logs on the host.
- `./dags` and `./plugins` are mounted into each Airflow container.

`docker compose down` retains named volumes. Adding `--volumes` deletes both
named volumes and all data in them.

## Health and startup

Airflow services wait for healthy Redis and PostgreSQL and for `airflow-init`
to complete. Health checks cover PostgreSQL, Redis, the webserver, scheduler,
worker, triggerer, and Flower.

Useful read-only checks:

```bash
docker compose ps
docker compose logs airflow-init
docker compose logs airflow-scheduler
docker compose logs airflow-worker
```

## Local security model

The checked-in configuration should be used only on an isolated development
machine:

- published ports bind on all host interfaces unless the host firewall blocks
  them;
- Airflow and PostgreSQL use predictable default credentials;
- Airflow basic API authentication is enabled;
- the Fernet key is empty, so Airflow secrets are not protected at rest;
- Portainer mounts `/var/run/docker.sock`, which provides host-level Docker
  control; and
- the Weather API key is committed and requests use plaintext HTTP.

For safer local use, bind web ports to `127.0.0.1`, remove Portainer if it is
not needed, provide non-default credentials and a stable secret Fernet key,
and move application credentials into Airflow Connections or a secrets
backend. Do not expose this Compose stack directly to a network.

## Version policy

The stack is not reproducibly pinned:

- Airflow is fixed at 2.2.4, an unsupported release.
- PostgreSQL uses the mutable `13` tag.
- Redis and Portainer use `latest`.
- Adminer has no version tag.

Upgrade Airflow as a migration rather than changing one image string. Airflow
3 changes DAG APIs, imports, service commands, and configuration. Pin all
images to tested versions (and preferably digests) once the migration target
has been validated.
