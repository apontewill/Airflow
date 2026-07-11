# Airflow and Postal Validation PoC

This repository contains the original Airflow weather examples and a standalone
proof-of-concept SaaS API for postal-code validation.

## Postal validation service

The service provides:

- country-specific normalization and format checks;
- exact existence and locality checks when reference data has been loaded;
- single and bulk (up to 100 items) endpoints;
- API-key authentication and a validation usage log;
- a repeatable GeoNames download/normalize/load process; and
- OpenAPI documentation at `http://localhost:8001/docs`.

See
[`services/postal-validation/ARCHITECTURE.md`](services/postal-validation/ARCHITECTURE.md)
for end-to-end ingestion, serving, decision-flow, data-model, and deployment
diagrams.

“First-world country” is not a defined or stable classification. This PoC uses
ISO alpha-2 codes for the IMF advanced-economy group as its explicit scope, plus
Liechtenstein. `GET /v1/countries` is the source of truth. Hong Kong (`HK`) and
Macao (`MO`) are reported separately because they do not use postal codes.
Puerto Rico (`PR`) is handled as an alias of the US system and `UK` as an alias
of `GB`.

Format validation only establishes that a value is structurally possible.
Existence validation requires country reference data. Responses state the
validation level (`format`, `reference`, or `unsupported`) so consumers do not
confuse the two.

### Run with Docker Compose

```bash
export POSTAL_API_KEYS="replace-with-a-random-secret"
docker compose up --build postal-validation-api
```

The API is exposed on port 8001 because the existing Portainer service uses
port 8000.

```bash
curl -X POST http://localhost:8001/v1/validate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: replace-with-a-random-secret' \
  -d '{"country":"CA","postal_code":"k1a0b1"}'
```

For local evaluation, the default key is `demo-key`. Do not use that default in
a deployed environment.

### Load postal reference data

The loader downloads a country export from
[GeoNames postal codes](https://download.geonames.org/export/zip/), validates
its tab-separated schema, normalizes each code, atomically replaces that
country's rows, and records the import count and source.

```bash
docker compose --profile postal-data run --rm postal-data-loader US CA GB DE
```

Downloaded files persist in the `postal-data` Docker volume. To re-import
existing files without downloading:

```bash
docker compose --profile postal-data run --rm postal-data-loader \
  --no-download US CA
```

GeoNames data is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); a production service
must preserve attribution and confirm whether an authoritative/licensed
national source is required for each market.

### Develop and test

```bash
cd services/postal-validation
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
uvicorn app.main:app --reload
```

SQLite is used by default for local development. Compose supplies a PostgreSQL
URL and reuses the existing Postgres container. The versioned PostgreSQL schema
is in `services/postal-validation/migrations/001_postal_validation.sql`; the PoC
also creates missing tables at application startup.

Before production use, replace environment-based API keys with hashed,
tenant-owned credentials, add rate limiting and quotas, run schema migrations
outside application startup, establish source freshness SLAs, and review
country-level data licensing and coverage.

## Existing Airflow environment

- Airflow UI: port 8080
- Adminer: port 8081 (`postgres:5432`, user/password `airflow`/`airflow`)
- Portainer: port 9000

The weather DAGs under `dags/` retain their original manual `WeatherData`
database setup.


