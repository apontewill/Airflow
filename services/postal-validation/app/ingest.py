"""Load GeoNames postal-code exports into the service database."""

import argparse
import csv
from io import TextIOWrapper
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import DataImport, PostalCode, engine, initialize_database
from app.validator import RULES, normalize_postal_code


SOURCE_TEMPLATE = "https://download.geonames.org/export/zip/{country}.zip"


def parse_row(row: list[str], country: str) -> PostalCode:
    if len(row) < 12:
        raise ValueError(f"Expected 12 columns, received {len(row)}")
    return PostalCode(
        country_code=country,
        postal_code=normalize_postal_code(country, row[1]),
        place_name=row[2] or None,
        admin_name=row[3] or None,
        admin_code=row[4] or None,
        latitude=float(row[9]) if row[9] else None,
        longitude=float(row[10]) if row[10] else None,
        source="GeoNames",
    )


def rows_from_zip(path: Path, country: str):
    with ZipFile(path) as archive:
        member = next(
            (name for name in archive.namelist() if name.lower().endswith(".txt")),
            None,
        )
        if not member:
            raise ValueError(f"{path} contains no text data")
        with archive.open(member) as binary:
            reader = csv.reader(TextIOWrapper(binary, encoding="utf-8"), delimiter="\t")
            for line_number, row in enumerate(reader, start=1):
                try:
                    yield parse_row(row, country)
                except (ValueError, IndexError) as exc:
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc


def download(country: str, data_dir: Path) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    destination = data_dir / f"{country}.zip"
    source = SOURCE_TEMPLATE.format(country=country)
    with urlopen(source, timeout=60) as response, destination.open("wb") as output:
        output.write(response.read())
    return destination


def import_country(country: str, path: Path, batch_size: int = 5_000) -> int:
    records = rows_from_zip(path, country)
    count = 0
    with Session(engine) as session, session.begin():
        session.execute(delete(PostalCode).where(PostalCode.country_code == country))
        batch: list[PostalCode] = []
        for record in records:
            batch.append(record)
            if len(batch) >= batch_size:
                session.add_all(batch)
                session.flush()
                count += len(batch)
                batch.clear()
        session.add_all(batch)
        count += len(batch)
        session.add(
            DataImport(country_code=country, source=str(path), row_count=count)
        )
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("countries", nargs="+", help="ISO alpha-2 country codes")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Use existing <data-dir>/<country>.zip files",
    )
    args = parser.parse_args()
    initialize_database()

    for raw_country in args.countries:
        country = raw_country.upper()
        if country not in RULES:
            parser.error(f"{country} is outside the configured scope")
        path = args.data_dir / f"{country}.zip"
        if not args.no_download:
            path = download(country, args.data_dir)
        count = import_country(country, path)
        print(f"{country}: imported {count:,} rows from {path}")


if __name__ == "__main__":
    main()
