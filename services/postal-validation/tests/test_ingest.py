from zipfile import ZipFile

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import PostalCode, engine, find_postal_code, initialize_database
from app.ingest import import_country


def test_imports_geonames_zip_and_normalizes_codes(tmp_path):
    archive_path = tmp_path / "CA.zip"
    row = "\t".join(
        [
            "CA",
            "K1A0B1",
            "Ottawa",
            "Ontario",
            "ON",
            "",
            "",
            "",
            "",
            "45.4207",
            "-75.7023",
            "1",
        ]
    )
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("CA.txt", f"{row}\n")

    initialize_database()
    assert import_country("CA", archive_path, batch_size=1) == 1
    matches = find_postal_code("CA", "K1A 0B1")
    assert len(matches) == 1
    assert matches[0].place_name == "Ottawa"
    assert matches[0].admin_code == "ON"

    with Session(engine) as session, session.begin():
        session.execute(delete(PostalCode).where(PostalCode.country_code == "CA"))
