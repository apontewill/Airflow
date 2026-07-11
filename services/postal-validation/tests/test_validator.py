import pytest

from app.validator import RULES, format_is_valid, normalize_country, normalize_postal_code


@pytest.mark.parametrize(
    ("country", "raw", "normalized"),
    [
        ("us", "123456789", "12345-6789"),
        ("CA", "k1a0b1", "K1A 0B1"),
        ("GB", "sw1a1aa", "SW1A 1AA"),
        ("JP", "1000001", "100-0001"),
        ("PT", "1000001", "1000-001"),
        ("NL", "1012js", "1012 JS"),
        ("UK", "EC1A1BB", "EC1A 1BB"),
    ],
)
def test_normalizes_and_validates(country, raw, normalized):
    assert normalize_postal_code(country, raw) == normalized
    assert format_is_valid(country, normalized)


@pytest.mark.parametrize(
    ("country", "postal_code"),
    [("US", "ABCDE"), ("CA", "D1A 0B1"), ("DE", "1234"), ("GB", "12345")],
)
def test_rejects_invalid_formats(country, postal_code):
    assert not format_is_valid(country, postal_code)


def test_country_aliases():
    assert normalize_country("uk") == "GB"
    assert normalize_country("PR") == "US"


@pytest.mark.parametrize(("country", "rule"), RULES.items())
def test_documented_example_is_valid(country, rule):
    assert format_is_valid(country, rule.example)
