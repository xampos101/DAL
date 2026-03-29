"""ORM helpers for Pydantic: avoid reading SQLAlchemy DeclarativeBase `.metadata`."""

from __future__ import annotations

from typing import Any


def orm_columns_dict(instance: object) -> dict[str, Any]:
    """Build a dict from mapped columns only (no relationships, no ``.metadata``)."""
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(instance).mapper
    return {attr.key: getattr(instance, attr.key) for attr in mapper.column_attrs}
