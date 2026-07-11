# Postal Validation: Ingestion to API Serving

This document shows how external postal reference data becomes an authenticated
validation response. The service always identifies whether a result came from a
format rule or an exact reference-data lookup.

## End-to-end architecture

```mermaid
flowchart LR
    subgraph Sources["Reference-data sources"]
        GN["GeoNames country ZIP export<br/>CC BY 4.0"]
        NS["Future authoritative<br/>national sources"]
    end

    subgraph Ingestion["Batch ingestion process"]
        CLI["postal-data-loader<br/>python -m app.ingest"]
        DL["Download country archive"]
        PARSE["Read UTF-8 TSV<br/>validate 12-column schema"]
        NORM["Normalize country and<br/>postal-code representation"]
        REPLACE["Atomic country refresh<br/>delete old + insert new"]
        AUDIT["Record data_imports<br/>source, rows, timestamp"]

        CLI --> DL --> PARSE --> NORM --> REPLACE
        REPLACE --> AUDIT
    end

    subgraph Storage["PostgreSQL / local SQLite"]
        PC[("postal_codes<br/>country + postal-code index")]
        DI[("data_imports<br/>ingestion audit")]
        VR[("validation_requests<br/>usage audit")]
    end

    subgraph Serving["FastAPI serving path"]
        CLIENT["Business client"]
        AUTH["X-API-Key authentication"]
        API["/v1/validate<br/>/v1/validate/bulk"]
        RULE["Normalize input and<br/>apply country format rule"]
        LOOKUP{"Country reference<br/>data loaded?"}
        EXACT["Exact indexed lookup"]
        FORMAT["Format-only result"]
        RESPONSE["Typed response<br/>level + reason + locations"]

        CLIENT --> AUTH --> API --> RULE --> LOOKUP
        LOOKUP -- "yes" --> EXACT --> RESPONSE
        LOOKUP -- "no" --> FORMAT --> RESPONSE
        RESPONSE --> CLIENT
    end

    GN --> CLI
    NS -. "future adapter" .-> CLI
    REPLACE --> PC
    AUDIT --> DI
    EXACT --> PC
    API --> VR
```

## Ingestion sequence

The loader processes each requested ISO alpha-2 country independently. A failed
country transaction rolls back without deleting its previously loaded data.

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    participant Loader as postal-data-loader
    participant Source as GeoNames
    participant Archive as Country ZIP
    participant DB as PostgreSQL

    Operator->>Loader: Run loader with country list
    loop For each country
        Loader->>Loader: Confirm country is in configured scope
        Loader->>Source: GET /export/zip/{country}.zip
        Source-->>Loader: ZIP archive
        Loader->>Archive: Open first .txt member as UTF-8 TSV
        loop For each row
            Loader->>Loader: Validate 12 fields
            Loader->>Loader: Normalize postal code
            Loader->>Loader: Map locality, admin code, coordinates
        end
        Loader->>DB: BEGIN
        Loader->>DB: Delete existing country rows
        loop Batches of 5,000
            Loader->>DB: Insert normalized postal rows
        end
        Loader->>DB: Insert data_imports audit row
        Loader->>DB: COMMIT
        Loader-->>Operator: Report imported row count
    end
```

Run it through Compose:

```bash
docker compose --profile postal-data run --rm postal-data-loader US CA GB DE
```

To use archives already stored in the `postal-data` volume:

```bash
docker compose --profile postal-data run --rm postal-data-loader \
  --no-download US CA
```

## API validation decision flow

```mermaid
flowchart TD
    REQ["Request<br/>country + postal_code"] --> KEY{"Valid X-API-Key?"}
    KEY -- "no" --> UNAUTH["401 Unauthorized"]
    KEY -- "yes" --> COUNTRY["Normalize country alias<br/>UK→GB, PR→US, EL→GR"]
    COUNTRY --> SYSTEM{"Country status"}
    SYSTEM -- "No postal system<br/>HK or MO" --> NOPOST["valid=false<br/>level=unsupported"]
    SYSTEM -- "Outside PoC scope" --> UNSUP["valid=false<br/>level=unsupported"]
    SYSTEM -- "Supported" --> CODE["Uppercase and normalize<br/>spaces / hyphens"]
    CODE --> REGEX{"Matches country format?"}
    REGEX -- "no" --> INVALID["valid=false<br/>level=format"]
    REGEX -- "yes" --> LOADED{"Any reference rows<br/>for country?"}
    LOADED -- "no" --> VALIDFORMAT["valid=true<br/>level=format<br/>existence not asserted"]
    LOADED -- "yes" --> FOUND{"Exact country + code<br/>match?"}
    FOUND -- "no" --> NOTFOUND["valid=false<br/>level=reference"]
    FOUND -- "yes" --> VALIDREF["valid=true<br/>level=reference<br/>return locality data"]

    NOPOST --> LOG["Record validation_requests"]
    UNSUP --> LOG
    INVALID --> LOG
    VALIDFORMAT --> LOG
    NOTFOUND --> LOG
    VALIDREF --> LOG
    LOG --> RES["Return typed JSON response"]
```

### Example response before reference data is loaded

```json
{
  "country": "CA",
  "postal_code": "K1A 0B1",
  "valid": true,
  "validation_level": "format",
  "reason": "Format is valid; reference data is not loaded for this country",
  "locations": []
}
```

### Example response after reference data is loaded

```json
{
  "country": "CA",
  "postal_code": "K1A 0B1",
  "valid": true,
  "validation_level": "reference",
  "reason": "Found in reference data",
  "locations": [
    {
      "place_name": "Ottawa",
      "admin_name": "Ontario",
      "admin_code": "ON",
      "latitude": 45.4207,
      "longitude": -75.7023
    }
  ]
}
```

## Data model

```mermaid
erDiagram
    POSTAL_CODES {
        bigint id PK
        varchar country_code "indexed with postal_code"
        varchar postal_code "normalized"
        varchar place_name
        varchar admin_name
        varchar admin_code
        float latitude
        float longitude
        varchar source
    }

    DATA_IMPORTS {
        bigint id PK
        varchar country_code
        varchar source
        integer row_count
        timestamptz imported_at
    }

    VALIDATION_REQUESTS {
        bigint id PK
        varchar api_key_id "truncated SHA-256 identifier"
        varchar country_code
        varchar postal_code
        varchar result
        timestamptz created_at
    }
```

`data_imports` and `validation_requests` are audit tables; they intentionally do
not own postal rows through foreign keys. Country refreshes can therefore
replace reference rows without removing historical import or request records.

## Deployment view

```mermaid
flowchart TB
    subgraph Compose["Docker Compose"]
        API["postal-validation-api<br/>host :8001 → container :8000"]
        LOADER["postal-data-loader<br/>postal-data profile"]
        PG[("postgres:13<br/>airflow database")]
        VOL[("postal-data volume<br/>downloaded archives")]

        API --> PG
        LOADER --> PG
        LOADER --> VOL
    end

    USER["Business API consumer"] -->|"HTTPS in production<br/>X-API-Key"| API
    OPS["Operator / scheduler"] --> LOADER
    SOURCE["GeoNames"] --> LOADER
```

The PoC reuses the repository's PostgreSQL container. Production should use
managed migrations, tenant-owned hashed credentials, request quotas, source
freshness monitoring, and a scheduler for country refreshes.
