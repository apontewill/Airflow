# Troubleshooting

## Permission denied under `/opt/airflow/logs`

**Cause:** On Linux, bind-mounted directories can be created with ownership
that does not match the Airflow container user.

**Action:**

```bash
printf 'AIRFLOW_UID=%s\n' "$(id -u)" > .env
mkdir -p logs plugins
docker compose up airflow-init
```

Then restart the stack. `images/ProblemVolumes.PNG` shows an example of this
failure.

> The repository does not currently ignore `.env`. Keep it untracked,
> especially if you add credentials.

## A DAG is visible but does not run

New DAGs start paused. Unpause the selected DAG in the Airflow UI. Only
`ETLWeatherPrintAirflow2` has a schedule; the other three require a manual
trigger.

## DAG import fails

Inspect scheduler output:

```bash
docker compose logs airflow-scheduler
```

The DAG files require Pendulum, Requests, Pandas, and—for database DAGs—
psycopg2. There is no dependency manifest or custom image, so an image change
can cause missing-import failures.

## Weather API extraction fails

Likely causes include:

- the committed key has been revoked or exhausted;
- the endpoint is unavailable;
- the container cannot reach the internet; or
- the API returned a non-success response.

The current extractors have no timeout, `raise_for_status()`, retry policy, or
response-schema validation. As a result, an HTTP failure may appear later as a
transform error. Inspect the extract task log and migrate the request code as
recommended in the [code review](code-review.md).

## `database "WeatherData" does not exist`

Compose creates only the `airflow` database. Follow the
[database setup](getting-started.md#4-prepare-the-weather-database).

## `relation "temperature" does not exist`

Create the expected table in `WeatherData`, not in the `airflow` metadata
database. The loaders insert into unqualified table name `temperature`.

## A connection error becomes `UnboundLocalError`

The two PostgreSQL loaders define `connection` inside a `try` and reference it
from `except` and `finally`. If `psycopg2.connect` fails before assignment,
cleanup raises a second error. The useful first error may still appear earlier
in the task log. Initialize resources before the `try` or use context managers
to fix the code.

## Duplicate or conflicting rows

The current load tasks perform unconditional inserts. Clearing a load task,
retrying a DAG run, or manually rerunning the same reading can create a
duplicate—or violate the recommended unique constraint. Make the operation
idempotent with a unique key and `INSERT ... ON CONFLICT`.

## Timestamps look wrong

The transformer calls `datetime.fromtimestamp`, which uses the container's
timezone, and then appends `+02:00`. This is wrong whenever the container is not
already at that offset and does not account for daylight-saving changes.
Until fixed, treat stored timestamps as unreliable. The source response's
`location.tz_id` or an aware UTC conversion should be used.

## Portainer credentials do not work

The old README listed `admin/password`, but Compose does not configure those
credentials. Portainer may require first-run account creation, depending on
the image version and existing volume. Because the image uses `latest`, its
behavior may also drift between pulls.
