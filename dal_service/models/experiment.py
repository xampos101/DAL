"""Experiment ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dal_service.models import Base


class Experiment(Base):
    """Represents an experiment definition and metadata."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Nullable text fields
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end: Mapped[datetime | None] = mapped_column(
        "end",
        DateTime(timezone=True),
        nullable=True,
    )
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True, default="new")

    # JSONB fields (Python attribute name avoids clashing with DeclarativeBase.metadata)
    experiment_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    creator: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Workflow references (array of workflow UUIDs)
    workflow_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        default=list,
    )

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    workflows: Mapped[list["Workflow"]] = relationship(
        "Workflow",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

