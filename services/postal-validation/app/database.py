"""Database models and lookup helpers for postal reference data."""

from datetime import datetime, timezone
import os

from sqlalchemy import DateTime, Float, Index, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./postal_validation.db")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


class Base(DeclarativeBase):
    pass


class PostalCode(Base):
    __tablename__ = "postal_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=False)
    place_name: Mapped[str | None] = mapped_column(String(180))
    admin_name: Mapped[str | None] = mapped_column(String(180))
    admin_code: Mapped[str | None] = mapped_column(String(32))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(64), default="unknown")

    __table_args__ = (
        Index("ix_postal_country_code", "country_code", "postal_code"),
    )


class ValidationRequest(Base):
    __tablename__ = "validation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_key_id: Mapped[str] = mapped_column(String(16), default="demo")
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=False)
    result: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class DataImport(Base):
    __tablename__ = "data_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def initialize_database() -> None:
    Base.metadata.create_all(engine)


def find_postal_code(country: str, postal_code: str) -> list[PostalCode]:
    with Session(engine) as session:
        statement = select(PostalCode).where(
            PostalCode.country_code == country,
            PostalCode.postal_code == postal_code,
        )
        return list(session.scalars(statement).all())


def has_reference_data(country: str) -> bool:
    with Session(engine) as session:
        statement = select(PostalCode.id).where(PostalCode.country_code == country).limit(1)
        return session.scalar(statement) is not None


def record_request(api_key_id: str, country: str, postal_code: str, result: str) -> None:
    with Session(engine) as session:
        session.add(
            ValidationRequest(
                api_key_id=api_key_id,
                country_code=country,
                postal_code=postal_code,
                result=result,
            )
        )
        session.commit()
