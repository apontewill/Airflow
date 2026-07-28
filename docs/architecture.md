# Architecture and data flow

## Runtime topology

```text
                          +-------------------+
                          |  Airflow UI :8080 |
                          +---------+---------+
                                    |
                     schedules work | reads state
                                    v
+-------------+    jobs     +-------+--------+    results     +------------+
| Scheduler   +------------>| Celery worker  +--------------->| PostgreSQL |
+-------------+             +-------+--------+                | `airflow`  |
                                    ^                         +------------+
                                    |
                              +-----+-----+
                              | Redis     |
                              | broker    |
                              +-----------+

Worker: WeatherAPI -> extract -> transform -> log and/or `WeatherData`
```

The Compose stack also includes:

- **Triggerer** for deferred Airflow tasks.
- **Flower** for Celery monitoring.
- **Adminer** for database administration.
- **Portainer** for Docker administration.

All Airflow containers mount `dags/`, `logs/`, and `plugins/` from the host.
PostgreSQL and Portainer use named volumes.

## ETL data flow

### Extract

Every DAG makes the same WeatherAPI current-conditions request for Berlin with
air-quality data disabled. The classic DAG serializes the response to a JSON
string and pushes a named XCom. TaskFlow DAGs return the decoded JSON object,
which Airflow passes through XCom automatically.

### Transform

`dags/transformer.py`:

1. parses the incoming JSON string;
2. flattens nested fields with `pandas.json_normalize`;
3. builds a timestamp from `location.localtime_epoch`;
4. renames selected columns; and
5. returns a JSON array in records orientation.

The output contract is:

```json
[
  {
    "location": "Berlin",
    "temp_c": 20.0,
    "wind_kph": 10.0,
    "timestamp": "2026-07-28T02:00:00+02:00"
  }
]
```

The values above are illustrative. The current timestamp implementation is not
timezone-safe: it uses the container timezone and appends a fixed `+02:00`
offset. Consumers must not assume the timestamp identifies the correct instant.

### Load

The load target depends on the DAG:

- write the transformed JSON to an Airflow task log;
- print the decoded records to a task log;
- insert the first record into
  `temperature(location, temp_c, wind_kph, time)`; or
- fan out to both PostgreSQL and a print task.

The PostgreSQL loaders connect directly with `psycopg2`. They do not use the
Airflow connection shown in `images/Postgres_connection.PNG`.

## Repository map

```text
.
├── dags/
│   ├── 00_ETLWeatherPrintAirflow2.py      classic operator example
│   ├── 01-ETLWeatherPrint.py              TaskFlow print example
│   ├── 02-ETLWeatherPostgres.py           TaskFlow PostgreSQL example
│   ├── 03-ETLWeatherPostgresAndPrint.py   TaskFlow fan-out example
│   └── transformer.py                     shared response transformation
├── docs/                                  project documentation
├── images/                                UI and troubleshooting screenshots
├── docker-compose.yml                     local Airflow cluster
└── README.md                              project landing page
```

## Important boundaries

- The stack is explicitly local-development infrastructure.
- `airflow` and `WeatherData` are separate databases in one PostgreSQL service.
- The Compose file creates only `airflow`; weather storage needs manual setup.
- The DAG directory contains four independently registered pipelines, not four
  stages of one pipeline.
- The images are historical aids. They are not executable configuration and
  can differ from the implementation.
