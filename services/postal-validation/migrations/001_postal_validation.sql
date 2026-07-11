CREATE TABLE IF NOT EXISTS postal_codes (
    id BIGSERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL,
    postal_code VARCHAR(16) NOT NULL,
    place_name VARCHAR(180),
    admin_name VARCHAR(180),
    admin_code VARCHAR(32),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    source VARCHAR(64) NOT NULL DEFAULT 'unknown'
);

CREATE INDEX IF NOT EXISTS ix_postal_country_code
    ON postal_codes (country_code, postal_code);

CREATE TABLE IF NOT EXISTS validation_requests (
    id BIGSERIAL PRIMARY KEY,
    api_key_id VARCHAR(16) NOT NULL DEFAULT 'demo',
    country_code VARCHAR(2) NOT NULL,
    postal_code VARCHAR(16) NOT NULL,
    result VARCHAR(24) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_imports (
    id BIGSERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL,
    source VARCHAR(255) NOT NULL,
    row_count INTEGER NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
