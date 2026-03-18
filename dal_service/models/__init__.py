"""SQLAlchemy ORM models for the DAL service."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


__all__ = ["Base"]


