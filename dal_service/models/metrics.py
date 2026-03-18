"""ORM models for metrics and related tables."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID, DOUBLE_PRECISION, BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dal_service.models import Base


class Metric(Base):
    """Stores performance metrics for experiments and workflows."""

    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Parent reference (polymorphic: workflow or experiment)
    parent_type: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Metric details
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str | None] = mapped_column(Text, nullable=True)
    semantic_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    produced_by_task: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Records (JSONB for small series)
    records: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Metadata (Python attribute name avoids clashing with DeclarativeBase.metadata)
    metric_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

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
    records_rel: Mapped[list["MetricRecord"]] = relationship(
        "MetricRecord",
        back_populates="metric",
        cascade="all, delete-orphan",
    )
    aggregation: Mapped["MetricAggregation | None"] = relationship(
        "MetricAggregation",
        back_populates="metric",
        uselist=False,
        cascade="all, delete-orphan",
    )


class MetricRecord(Base):
    """Normalized metric records for large series."""

    __tablename__ = "metric_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metrics.id", ondelete="CASCADE"),
        nullable=False,
    )

    value: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )

    metric: Mapped[Metric] = relationship(
        "Metric",
        back_populates="records_rel",
    )


class MetricAggregation(Base):
    """Cached aggregation computations for a metric."""

    __tablename__ = "metric_aggregations"

    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metrics.id", ondelete="CASCADE"),
        primary_key=True,
    )

    count: Mapped[int] = mapped_column(BIGINT, nullable=False, default=0)
    sum: Mapped[float | None] = mapped_column(DOUBLE_PRECISION, nullable=True)
    min: Mapped[float | None] = mapped_column(DOUBLE_PRECISION, nullable=True)
    max: Mapped[float | None] = mapped_column(DOUBLE_PRECISION, nullable=True)
    average: Mapped[float | None] = mapped_column(DOUBLE_PRECISION, nullable=True)
    median: Mapped[float | None] = mapped_column(DOUBLE_PRECISION, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )

    metric: Mapped[Metric] = relationship(
        "Metric",
        back_populates="aggregation",
    )

