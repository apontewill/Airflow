"""Country-specific postal-code normalization and format validation."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PostalRule:
    name: str
    pattern: str
    example: str
    compact: bool = True


# ISO 3166-1 alpha-2 codes for economies classified as advanced by the IMF.
# HK and MO deliberately appear in NO_POSTAL_CODE because they do not use codes.
RULES: dict[str, PostalRule] = {
    "AD": PostalRule("Andorra", r"AD\d{3}", "AD500"),
    "AT": PostalRule("Austria", r"\d{4}", "1010"),
    "AU": PostalRule("Australia", r"\d{4}", "2000"),
    "BE": PostalRule("Belgium", r"\d{4}", "1000"),
    "CA": PostalRule("Canada", r"[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTVWXYZ]\d[ABCEGHJ-NPRSTVWXYZ]\d", "K1A 0B1"),
    "CH": PostalRule("Switzerland", r"\d{4}", "8001"),
    "CY": PostalRule("Cyprus", r"\d{4}", "1010"),
    "CZ": PostalRule("Czechia", r"\d{5}", "110 00"),
    "DE": PostalRule("Germany", r"\d{5}", "10115"),
    "DK": PostalRule("Denmark", r"\d{4}", "1050"),
    "EE": PostalRule("Estonia", r"\d{5}", "10111"),
    "ES": PostalRule("Spain", r"\d{5}", "28001"),
    "FI": PostalRule("Finland", r"\d{5}", "00100"),
    "FR": PostalRule("France", r"\d{5}", "75001"),
    "GB": PostalRule(
        "United Kingdom",
        r"(GIR0AA|(?:[A-Z]{1,2}\d[A-Z\d]?|\d[A-Z]{2})\d[A-Z]{2})",
        "SW1A 1AA",
    ),
    "GR": PostalRule("Greece", r"\d{5}", "105 58"),
    "IE": PostalRule("Ireland", r"(?:D6W|[AC-FHKNPRTV-Y]\d{2})[0-9AC-FHKNPRTV-Y]{4}", "D02 X285"),
    "IL": PostalRule("Israel", r"\d{7}", "9199907"),
    "IS": PostalRule("Iceland", r"\d{3}", "101"),
    "IT": PostalRule("Italy", r"\d{5}", "00118"),
    "JP": PostalRule("Japan", r"\d{7}", "100-0001"),
    "KR": PostalRule("South Korea", r"\d{5}", "03051"),
    "LI": PostalRule("Liechtenstein", r"(?:948[5-9]|949[0-8])", "9490"),
    "LT": PostalRule("Lithuania", r"\d{5}", "01100"),
    "LU": PostalRule("Luxembourg", r"\d{4}", "1234"),
    "LV": PostalRule("Latvia", r"LV\d{4}", "LV-1050"),
    "MT": PostalRule("Malta", r"[A-Z]{3}\d{4}", "VLT 1117"),
    "NL": PostalRule("Netherlands", r"\d{4}[A-Z]{2}", "1012 JS"),
    "NO": PostalRule("Norway", r"\d{4}", "0150"),
    "NZ": PostalRule("New Zealand", r"\d{4}", "6011"),
    "PT": PostalRule("Portugal", r"\d{7}", "1000-001"),
    "SE": PostalRule("Sweden", r"\d{5}", "111 22"),
    "SG": PostalRule("Singapore", r"\d{6}", "018956"),
    "SI": PostalRule("Slovenia", r"\d{4}", "1000"),
    "SK": PostalRule("Slovakia", r"\d{5}", "811 01"),
    "SM": PostalRule("San Marino", r"4789\d", "47890"),
    "TW": PostalRule("Taiwan", r"\d{3}(?:\d{2,3})?", "100"),
    "US": PostalRule("United States and Puerto Rico", r"\d{5}(?:\d{4})?", "90210"),
}

NO_POSTAL_CODE = {
    "HK": "Hong Kong does not use a postal-code system",
    "MO": "Macao does not use a postal-code system",
}

ALIASES = {"UK": "GB", "EL": "GR", "PR": "US"}


def normalize_country(country: str) -> str:
    code = country.strip().upper()
    return ALIASES.get(code, code)


def normalize_postal_code(country: str, postal_code: str) -> str:
    code = normalize_country(country)
    compact = re.sub(r"[\s-]+", "", postal_code.strip().upper())
    if code == "CA" and len(compact) == 6:
        return f"{compact[:3]} {compact[3:]}"
    if code == "GB" and len(compact) >= 5:
        return f"{compact[:-3]} {compact[-3:]}"
    if code == "IE" and len(compact) == 7:
        return f"{compact[:3]} {compact[3:]}"
    if code in {"CZ", "GR", "SE", "SK"} and len(compact) == 5:
        return f"{compact[:3]} {compact[3:]}"
    if code == "JP" and len(compact) == 7:
        return f"{compact[:3]}-{compact[3:]}"
    if code == "LV" and len(compact) == 6:
        return f"{compact[:2]}-{compact[2:]}"
    if code == "MT" and len(compact) == 7:
        return f"{compact[:3]} {compact[3:]}"
    if code == "NL" and len(compact) == 6:
        return f"{compact[:4]} {compact[4:]}"
    if code == "PT" and len(compact) == 7:
        return f"{compact[:4]}-{compact[4:]}"
    if code == "US" and len(compact) == 9:
        return f"{compact[:5]}-{compact[5:]}"
    return compact


def format_is_valid(country: str, postal_code: str) -> bool:
    code = normalize_country(country)
    rule = RULES.get(code)
    if not rule:
        return False
    compact = re.sub(r"[\s-]+", "", postal_code.strip().upper())
    return re.fullmatch(rule.pattern, compact, flags=re.ASCII) is not None
