# Architecture and data flow

## Runtime topology

```text
                           +----------------------+
                           | API server/UI :8080  |
                           +-----------+----------+
                                       |
                         state and execution API
                                       |
+---------------+ serialized DAGs +----v-----+ jobs  +---------------+
| DAG processor +--------------->| Scheduler +------>| Celery worker |
+---------------+                +----------+        +-------+-------+
                                                               ^
                                                               |
                                                          +----+------+
                                                          | Redis     |
                                                          | broker    |
                                                          +-----------+

Worker: WeatherAPI -> extract -> transform -> log and/or `WeatherData`
```

Airflow 3 separates DAG parsing into `airflow-dag-processor` and serves its UI,
REST API, and task execution API through `airflow-apiserver`. The stack also
includes a triggerer for deferred tasks and optional Flower monitoring.

All Airflow containers mount `dags/`, `logs/`, `config/`, and `plugins/` from
the host. PostgreSQL stores both the Airflow metadata and weather databases in
one named volume.

## ETL data flow

### Extract

`dags/weather.py` makes an HTTPS WeatherAPI current-conditions request for
Berlin with air-quality data disabled. It reads the API key from
`WEATHER_API_KEY`, applies connect/read timeouts, checks HTTP status, and
validates the response before returning it.

The classic DAG demonstrates an explicit named XCom. TaskFlow DAGs return the
decoded JSON object, which Airflow passes through XCom automatically.

### Transform

`dags/transformer.py`:

1. accepts the decoded response or a JSON string;
2. validates the required location and current-weather fields;
3. converts `location.localtime_epoch` from UTC to `location.tz_id`; and
4. returns a typed list containing one weather record.

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

### Load

The load target depends on the DAG:

- log or print the normalized records;
- upsert the first record into
  `temperature(location, temp_c, wind_kph, time)`; or
- fan out to both PostgreSQL and a print task.

The database helper uses context-managed psycopg2 resources and an idempotent
`ON CONFLICT (location, time) DO UPDATE`. PostgreSQL creates the weather
database and primary key from the versioned initialization SQL.

## Repository map

```text
.
├── dags/
│   ├── 00_ETLWeatherPrintAirflow2.py      classic operator example
│   ├── 01-ETLWeatherPrint.py              TaskFlow print example
│   ├── 02-ETLWeatherPostgres.py           TaskFlow PostgreSQL example
│   ├── 03-ETLWeatherPostgresAndPrint.py   TaskFlow fan-out example
│   ├── transformer.py                     response transformation
│   └── weather.py                         API and database operations
├── docker/postgres-init/                  weather database initialization
├── docs/                                  project documentation
├── images/                                historical UI screenshots
├── docker-compose.yml                     Airflow 3 local cluster
└── README.md                              project landing page
```

## Important boundaries

- The stack is local-development infrastructure, not a production deployment.
- `airflow` and `WeatherData` are separate databases in one PostgreSQL service.
- Initialization SQL runs only when the PostgreSQL volume is first created.
- The four DAG files register independent pipelines, not stages of one DAG.
- Screenshots are historical aids and can differ from current Airflow 3 UI.
