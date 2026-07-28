SELECT 'CREATE DATABASE "WeatherData"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'WeatherData')\gexec

\connect WeatherData

CREATE TABLE IF NOT EXISTS temperature (
    location TEXT NOT NULL,
    temp_c DOUBLE PRECISION NOT NULL,
    wind_kph DOUBLE PRECISION NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (location, time)
);
