"""Pydantic schemas for experiments."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExperimentBase(BaseModel):
    """Shared fields for experiment create/update."""

    name: str | None = None
    intent: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    status: str | None = None
    model: str | None = None
    comment: str | None = None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="experiment_metadata",
    )
    creator: dict[str, Any] | None = None


class ExperimentCreate(ExperimentBase):
    """Payload for creating a new experiment."""

    pass


class ExperimentUpdate(ExperimentBase):
    """Payload for partially updating an experiment."""

    pass


class ExperimentRead(ExperimentBase):
    """Experiment representation returned to clients."""

    id: uuid.UUID
    workflow_ids: list[uuid.UUID] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ExperimentListItem(ExperimentRead):
    """Optional slimmer representation for experiment lists."""

    pass

