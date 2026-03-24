"""Pydantic schemas for workflows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class WorkflowBase(BaseModel):
    """Shared fields for workflow create/update."""

    name: str | None = None
    status: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    comment: str | None = None
    parameters: list[dict[str, Any]] | None = None
    tasks: list[dict[str, Any]] | None = None
    input_datasets: list[dict[str, Any]] | None = None
    output_datasets: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="workflow_metadata",
    )
    metric_ids: list[uuid.UUID] | None = None
    metrics: list[dict[str, Any]] | None = None


class WorkflowCreate(WorkflowBase):
    """Payload for creating a new workflow."""

    experiment_id: uuid.UUID = Field(validation_alias=AliasChoices("experiment_id", "experimentId"))
    name: str


class WorkflowUpdate(WorkflowBase):
    """Payload for partially updating a workflow."""

    pass


class WorkflowRead(WorkflowBase):
    """Workflow representation returned to clients."""

    id: uuid.UUID
    experiment_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

