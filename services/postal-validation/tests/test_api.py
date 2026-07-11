from fastapi.testclient import TestClient

from app.main import app


def test_health_does_not_require_authentication():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validation_requires_api_key():
    with TestClient(app) as client:
        response = client.post(
            "/v1/validate", json={"country": "US", "postal_code": "90210"}
        )
    assert response.status_code == 401


def test_validates_and_normalizes_format():
    with TestClient(app) as client:
        response = client.post(
            "/v1/validate",
            headers={"X-API-Key": "demo-key"},
            json={"country": "CA", "postal_code": "k1a0b1"},
        )
    assert response.status_code == 200
    assert response.json() == {
        "country": "CA",
        "postal_code": "K1A 0B1",
        "valid": True,
        "validation_level": "format",
        "reason": "Format is valid; reference data is not loaded for this country",
        "locations": [],
    }


def test_reports_countries_without_postal_codes():
    with TestClient(app) as client:
        response = client.post(
            "/v1/validate",
            headers={"X-API-Key": "demo-key"},
            json={"country": "HK", "postal_code": "000000"},
        )
    assert response.status_code == 200
    assert response.json()["validation_level"] == "unsupported"
    assert response.json()["valid"] is False


def test_bulk_limit_is_enforced():
    with TestClient(app) as client:
        response = client.post(
            "/v1/validate/bulk",
            headers={"X-API-Key": "demo-key"},
            json={"items": [{"country": "US", "postal_code": "90210"}] * 101},
        )
    assert response.status_code == 422
