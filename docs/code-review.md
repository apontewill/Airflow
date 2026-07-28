# Code review

Reviewed 28 July 2026. The review covers every tracked Python file,
`docker-compose.yml`, the existing README, ignore rules, and repository
screenshots. Findings are ordered by risk and impact.

## Summary

The lesson progression and task dependencies are easy to follow, and the
parameterized SQL insert avoids SQL injection. The main risks are credential
exposure, obsolete infrastructure, and clean-start failures. The project also
needs tests before behavior can be changed safely.

| Priority | Findings |
| --- | ---: |
| High | 6 |
| Medium | 6 |
| Low | 3 |

## High priority

### 1. Exposed API credential sent over HTTP

**Evidence:** Every DAG contains the same WeatherAPI key and calls
`http://api.weatherapi.com` (`dags/00...py:21-22`, `01...py:37-38`,
`02...py:42-43`, and `03...py:42-43`).

**Impact:** Repository readers can consume the key, and plaintext transport can
expose both the key and response in transit.

**Recommendation:** Revoke the committed key, purge it from usable history if
appropriate, use HTTPS, and load a replacement from an Airflow Connection or
secrets backend.

### 2. Management interfaces expose sensitive local capabilities

**Evidence:** Airflow, Adminer, Flower, and Portainer publish ports without a
loopback address (`docker-compose.yml:87-91`, `104-108`, `259-263`, and
`275-283`). Portainer mounts the Docker socket.

**Impact:** The interfaces bind to all host interfaces by default. A Portainer
compromise can control Docker and effectively the host.

**Recommendation:** Bind development ports to `127.0.0.1`, remove Portainer
when unnecessary, and never expose this stack directly to an untrusted network.

### 3. Airflow version is end-of-life

**Evidence:** Compose pins `apache/airflow:2.2.4`
(`docker-compose.yml:26-27,47`). Airflow 2 reached EOL on 22 April 2026
according to the
[official support table](https://airflow.apache.org/docs/apache-airflow/stable/installation/supported-versions.html).

**Impact:** The runtime receives no security fixes. Updating only the image tag
will break code: all DAGs use `schedule_interval`, which Airflow 3 removed, and
the classic DAG uses a legacy operator import.

**Recommendation:** Plan an explicit Airflow 3 migration. Change DAG imports
and scheduling APIs, update the Compose topology/configuration, pin current
providers and constraints, and test DAG parsing and execution. The
[official upgrade guide](https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html)
should be the migration baseline.

### 4. PostgreSQL DAGs fail on a clean deployment

**Evidence:** Compose creates only database `airflow`
(`docker-compose.yml:73-80`), while both loaders connect to `WeatherData` and
insert into `temperature` (`dags/02...py:79-89`, `03...py:78-88`).

**Impact:** The database DAGs cannot succeed until undocumented manual state
exists.

**Recommendation:** Version a migration or initialization script that creates
the database, table, constraints, and grants. Run it during local initialization
or through a dedicated migration command.

### 5. Database failures can be masked by cleanup errors

**Evidence:** `connection` is assigned inside `try`, then referenced in
`except` and `finally` in both PostgreSQL loaders (`dags/02...py:79-110` and
`03...py:78-109`).

**Impact:** If `psycopg2.connect` fails, cleanup can raise
`UnboundLocalError`, hiding the actionable connection error. The exception is
also wrapped with `raise Exception(error)`, losing useful type and traceback
context.

**Recommendation:** Use connection and cursor context managers, or initialize
both to `None` before `try`. Log context and use bare `raise`.

### 6. Airflow secrets are not encrypted at rest

**Evidence:** `AIRFLOW__CORE__FERNET_KEY` is empty
(`docker-compose.yml:55`).

**Impact:** Connection and Variable secrets stored in the metadata database are
not protected by a project-supplied encryption key, compounding the exposed
Adminer and default-credential risks.

**Recommendation:** Inject one stable, non-committed Fernet key or configure a
supported secrets backend. Rotate and re-save existing secrets afterward.

## Medium priority

### 7. HTTP requests lack production-safe failure handling

All extractors call `requests.get` without connect/read timeouts,
`raise_for_status()`, response validation, or task retries. A stalled endpoint
can occupy a worker, while an error JSON can fail later as a misleading
transform error. Add bounded timeouts, status/schema checks, and retry/backoff
for transient failures.

### 8. Timestamp conversion is incorrect

`dags/transformer.py:19` uses timezone-dependent
`datetime.fromtimestamp()` and appends literal `+02:00`. This can label a UTC
value as UTC+2 and ignores Berlin's winter offset. Convert the epoch as aware
UTC and either store UTC or convert with the API's `location.tz_id`.

### 9. Loads are not idempotent

Both database DAGs execute an unconditional `INSERT`. Retries, cleared tasks,
and repeated runs can duplicate a reading. Add a unique key such as
`(location, time)` and use `INSERT ... ON CONFLICT DO UPDATE` or `DO NOTHING`.

### 10. Runtime dependencies are not reproducible

There is no requirements/constraints file or custom image, while mutable image
tags are used for Redis, Adminer, PostgreSQL, and Portainer. Pin tested image
versions or digests and build a versioned Airflow image with locked Python
dependencies.

### 11. Logs contain more data than necessary

The transformer prints the full API response, and PostgreSQL extractors also
print the decoded response. This adds noise and can leak future sensitive
fields. Use structured Airflow logging with a minimal success summary.

### 12. No automated verification

There are no unit tests, DAG import tests, integration tests, or CI checks.
Refactoring duplicated extraction/load code or upgrading Airflow is risky
without them. Start with pure transformer tests, mocked HTTP tests, DAG-bag
import tests, and a PostgreSQL integration test for idempotency.

## Low priority

### 13. Type annotations do not match runtime values

Task parameters annotated as `dict` receive a list of dictionaries, and
`weather_json: json` refers to the imported module rather than a data type.
Define a `TypedDict` for a weather record and use `list[WeatherRecord]` (or
compatible syntax for the selected Python version).

### 14. Duplicate and misleading code obscures the lessons

The PostgreSQL DAGs have unused Pandas/datetime imports, duplicate connection
and request logic, the same misspelled registration variable, stale commented
code, and an inaccurate load docstring in DAG 03. Extract shared HTTP and
repository functions, remove dead code, and make task names/docstrings describe
actual behavior.

### 15. Repository hygiene is mismatched

`.gitignore` is a large Visual Studio template and does not ignore `.env`; no
`.dockerignore` exists. Replace it with focused Python/Airflow rules, keep a
safe `.env.example`, ignore local secrets, and restrict Docker build context.

## Recommended remediation order

### P0: security and access

1. Rotate the WeatherAPI key and switch to HTTPS.
2. Move secrets out of DAG source.
3. Bind interfaces to loopback and remove Docker socket access if unneeded.
4. Configure a stable Fernet key and non-default local credentials.

### P1: reproducible correctness

1. Add database migrations and idempotent writes.
2. Correct timezone conversion.
3. Preserve database exceptions and make cleanup safe.
4. Add request timeout, validation, and retry behavior.
5. Add dependency/image pinning and tests.

### P2: supported platform and maintainability

1. Migrate the stack and DAGs to a supported Airflow 3 release.
2. Consolidate repeated extractor and loader logic.
3. Correct types, naming, docstrings, and logging.
4. Add CI for formatting, linting, tests, and DAG imports.

## Positive observations

- The four files form a clear progression from explicit XCom to TaskFlow and
  fan-out.
- `catchup=False` is appropriate for current-weather requests.
- SQL values are passed as psycopg2 parameters rather than interpolated.
- DAG 03's two downstream tasks correctly express independent parallel work.
- The Compose file includes health checks and an initialization gate.
