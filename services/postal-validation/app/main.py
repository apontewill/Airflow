"""FastAPI application for postal-code validation."""

from contextlib import asynccontextmanager
import hashlib
import hmac
import os
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.database import (
    find_postal_code,
    has_reference_data,
    initialize_database,
    record_request,
)
from app.validator import (
    NO_POSTAL_CODE,
    RULES,
    format_is_valid,
    normalize_country,
    normalize_postal_code,
)


class ValidationInput(BaseModel):
    country: str = Field(min_length=2, max_length=2, examples=["US"])
    postal_code: str = Field(min_length=1, max_length=16, examples=["90210"])


class BulkValidationInput(BaseModel):
    items: list[ValidationInput] = Field(min_length=1, max_length=100)


class Location(BaseModel):
    place_name: str | None
    admin_name: str | None
    admin_code: str | None
    latitude: float | None
    longitude: float | None


class ValidationResult(BaseModel):
    country: str
    postal_code: str
    valid: bool
    validation_level: Literal["unsupported", "format", "reference"]
    reason: str
    locations: list[Location] = []


def configured_api_keys() -> list[str]:
    return [key.strip() for key in os.getenv("API_KEYS", "demo-key").split(",") if key.strip()]


def authenticate(x_api_key: Annotated[str | None, Header()] = None) -> str:
    for candidate in configured_api_keys():
        if x_api_key and hmac.compare_digest(x_api_key, candidate):
            return hashlib.sha256(candidate.encode()).hexdigest()[:16]
    raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


def validate_one(item: ValidationInput, api_key_id: str) -> ValidationResult:
    country = normalize_country(item.country)
    normalized = normalize_postal_code(country, item.postal_code)

    if country in NO_POSTAL_CODE:
        result = ValidationResult(
            country=country,
            postal_code=normalized,
            valid=False,
            validation_level="unsupported",
            reason=NO_POSTAL_CODE[country],
        )
    elif country not in RULES:
        result = ValidationResult(
            country=country,
            postal_code=normalized,
            valid=False,
            validation_level="unsupported",
            reason="Country is outside the configured PoC scope",
        )
    elif not format_is_valid(country, normalized):
        result = ValidationResult(
            country=country,
            postal_code=normalized,
            valid=False,
            validation_level="format",
            reason="Postal code does not match the country's format",
        )
    elif has_reference_data(country):
        matches = find_postal_code(country, normalized)
        result = ValidationResult(
            country=country,
            postal_code=normalized,
            valid=bool(matches),
            validation_level="reference",
            reason="Found in reference data" if matches else "Not found in reference data",
            locations=[
                Location(
                    place_name=row.place_name,
                    admin_name=row.admin_name,
                    admin_code=row.admin_code,
                    latitude=row.latitude,
                    longitude=row.longitude,
                )
                for row in matches
            ],
        )
    else:
        result = ValidationResult(
            country=country,
            postal_code=normalized,
            valid=True,
            validation_level="format",
            reason="Format is valid; reference data is not loaded for this country",
        )

    record_request(api_key_id, country, normalized, result.validation_level)
    return result


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Postal Validation API",
    version="0.1.0",
    description="PoC API for format and reference-data postal-code validation.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/countries")
def countries(_: Annotated[str, Depends(authenticate)]) -> dict:
    supported = [
        {"code": code, "name": rule.name, "example": rule.example}
        for code, rule in sorted(RULES.items())
    ]
    return {"supported": supported, "without_postal_codes": NO_POSTAL_CODE}


@app.post("/v1/validate", response_model=ValidationResult)
def validate(
    item: ValidationInput,
    api_key_id: Annotated[str, Depends(authenticate)],
) -> ValidationResult:
    return validate_one(item, api_key_id)


@app.post("/v1/validate/bulk", response_model=list[ValidationResult])
def validate_bulk(
    payload: BulkValidationInput,
    api_key_id: Annotated[str, Depends(authenticate)],
) -> list[ValidationResult]:
    return [validate_one(item, api_key_id) for item in payload.items]
