"""Pydantic schemas for metrics."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class MetricBase(BaseModel):
    """Shared fields for metric create/update."""

    experiment_id: uuid.UUID | None = None
    parent_type: Literal["experiment", "workflow"] | None = None
    parent_id: uuid.UUID | None = None
    name: str | None = None
    kind: str | None = None
    type: str | None = None
    semantic_type: str | None = None
    value: str | None = None
    produced_by_task: str | None = Field(
        default=None,
        validation_alias=AliasChoices("produced_by_task", "producedByTask"),
    )
    date: datetime | None = None
    records: list[dict[str, Any]] | None = None
    metric_metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metric_metadata"),
        serialization_alias="metadata",
    )


class MetricCreate(MetricBase):
    """Payload for creating a new metric."""

    experiment_id: uuid.UUID | None = None
    parent_type: Literal["experiment", "workflow"]
    parent_id: uuid.UUID
    name: str


class MetricUpdate(MetricBase):
    """Payload for partially updating a metric."""

    pass


class MetricRead(MetricBase):
    """Metric representation returned to clients."""

    id: uuid.UUID
    experiment_id: uuid.UUID
    parent_type: Literal["experiment", "workflow"]
    parent_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MetricRecordRead(BaseModel):
    """View for individual metric record entries."""

    id: uuid.UUID
    metric_id: uuid.UUID
    value: float
    timestamp: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MetricAggregationRead(BaseModel):
    """View for metric aggregation snapshot."""

    metric_id: uuid.UUID
    count: int
    sum: float | None = None
    min: float | None = None
    max: float | None = None
    average: float | None = None
    median: float | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

