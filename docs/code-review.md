# Code review

Updated 28 July 2026 after migration to Apache Airflow 3.3.0.

## Current assessment

The migration resolves the original repository's highest-risk defects:

- Airflow 2.2.4 was replaced by supported Airflow 3.3.0.
- all DAGs use the public `airflow.sdk` API or standard provider.
- the committed WeatherAPI key was removed and HTTPS is enforced.
- HTTP timeouts, status checks, and response validation were added.
- timestamp conversion now uses the API-provided IANA timezone.
- database cleanup uses context managers and preserves original exceptions.
- weather writes are idempotent.
- PostgreSQL schema initialization is versioned.
- management UIs and Docker socket exposure were removed.
- published ports bind to loopback.
- Fernet and API JWT secrets are required configuration.

## Remaining findings

### High: local Compose is not production infrastructure

The stack uses known internal PostgreSQL credentials, permits default Airflow
UI credentials, has no TLS, and stores secrets in a local environment file.
This matches the upstream quick-start's learning scope but is unsuitable for a
shared server.

**Recommendation:** For production, use the official Airflow Helm chart or a
managed service with external secret management, TLS, backups, monitoring,
network policy, and unique database credentials.

### Medium: no automated test suite or CI

The transformer, HTTP validation, database upsert, DAG imports, and task graph
are not continuously tested.

**Recommendation:** Add:

1. unit tests for timezone conversion and malformed payloads;
2. mocked HTTP tests for timeout and API errors;
3. DAG-bag import and graph tests on Airflow 3.3;
4. a PostgreSQL integration test for rerun idempotency; and
5. CI for formatting, linting, tests, and Compose validation.

### Medium: direct psycopg2 configuration bypasses Airflow Connections

Weather database settings are injected as environment variables. This is
functional for an external application database, but does not use Airflow's
connection management or a secrets backend.

**Recommendation:** Move the weather database configuration to an Airflow
Connection backed by the deployment's secret manager. Use a provider hook if
the educational goal expands to connection management.

### Medium: image tags are versions, not immutable digests

Airflow, PostgreSQL, and Redis use version tags. Re-pulling a tag can yield a
different image build.

**Recommendation:** Pin tested image digests in controlled deployments and use
an automated process to review updates.

### Low: classic DAG naming is historical

`ETLWeatherPrintAirflow2` remains named after Airflow 2 even though its imports
and scheduling API are Airflow 3 compatible.

**Recommendation:** Keep the ID stable for migration continuity, but describe
it as the classic `PythonOperator` lesson. Rename only with an intentional DAG
history migration.

### Low: stdout is used for lesson output

The TaskFlow print examples use `print`, which Airflow captures correctly but
offers less structure than application logging.

**Recommendation:** Introduce structured logging when the project moves beyond
the course example.

## Upgrade notes

Airflow 3 introduced architectural and API changes reflected in this
repository:

- `airflow-apiserver` replaces the Airflow 2 webserver service.
- `airflow-dag-processor` parses DAGs independently.
- workers communicate through the execution API.
- `schedule` replaces removed `schedule_interval`.
- DAG authoring imports come from `airflow.sdk`.
- `PythonOperator` comes from `apache-airflow-providers-standard`.

The local quick-start recreates its disposable metadata volume. Existing
Airflow 2 production metadata must follow the
[official upgrade sequence](https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html);
it must not be pointed directly at Airflow 3.3 from Airflow 2.2.

## Positive observations

- Stable DAG IDs preserve UI continuity.
- `catchup=False` is appropriate for current-weather requests.
- XCom usage clearly contrasts classic and TaskFlow styles.
- SQL parameters are bound safely.
- the fan-out DAG correctly expresses independent downstream work.
- shared API, transformation, and storage helpers remove prior duplication.
