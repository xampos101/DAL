"""Legacy query endpoints compatible with the Engine client."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dal_service.db.session import get_db
from dal_service.deps import require_access_token
from dal_service.utils.orm_columns import orm_columns_dict
from dal_service.models.experiment import Experiment
from dal_service.models.workflow import Workflow
from dal_service.models.metrics import Metric
from dal_service.schemas.experiment import ExperimentRead
from dal_service.schemas.workflow import WorkflowRead
from dal_service.schemas.metric import MetricRead

router = APIRouter(tags=["queries"])


@router.post("/experiments-query")
async def experiments_query(
    filters: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> list[ExperimentRead]:
    """Legacy experiments query.

    Engine expectations:
    - Request body is a plain dict (may include nested dicts like creator/metadata).
    - Unknown keys are ignored.
    - Response is a bare JSON array (no wrapper).
    """

    stmt = select(Experiment)

    for key, value in (filters or {}).items():
        if key == "id":
            stmt = stmt.where(Experiment.id == UUID(str(value)))
        elif key == "name":
            stmt = stmt.where(Experiment.name == value)
        elif key == "intent":
            stmt = stmt.where(Experiment.intent == value)
        elif key == "status":
            stmt = stmt.where(Experiment.status == value)
        elif key == "model":
            stmt = stmt.where(Experiment.model == value)
        elif key == "comment":
            stmt = stmt.where(Experiment.comment == value)
        elif key == "creator" and isinstance(value, dict):
            stmt = stmt.where(Experiment.creator.contains(value))
        elif key == "metadata" and isinstance(value, dict):
            stmt = stmt.where(Experiment.experiment_metadata.contains(value))
        else:
            # Unknown keys are ignored for legacy compatibility.
            continue

    result = await db.execute(stmt)
    experiments = result.scalars().all()
    return [ExperimentRead.model_validate(orm_columns_dict(e)) for e in experiments]


@router.post("/workflows-query")
async def workflows_query(
    filters: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> list[WorkflowRead]:
    """Legacy workflows query (bare list response). Unknown keys ignored."""

    stmt = select(Workflow)

    for key, value in (filters or {}).items():
        if key == "id":
            stmt = stmt.where(Workflow.id == UUID(str(value)))
        elif key in ("experiment_id", "experimentId"):
            stmt = stmt.where(Workflow.experiment_id == UUID(str(value)))
        elif key == "name":
            stmt = stmt.where(Workflow.name == value)
        elif key == "status":
            stmt = stmt.where(Workflow.status == value)
        elif key == "comment":
            stmt = stmt.where(Workflow.comment == value)
        elif key == "metadata" and isinstance(value, dict):
            stmt = stmt.where(Workflow.workflow_metadata.contains(value))
        else:
            continue

    result = await db.execute(stmt)
    workflows = result.scalars().all()
    return [WorkflowRead.model_validate(orm_columns_dict(w)) for w in workflows]


@router.post("/metrics-query")
async def metrics_query(
    filters: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> list[MetricRead]:
    """Legacy metrics query (bare list response). Unknown keys ignored."""

    stmt = select(Metric)

    for key, value in (filters or {}).items():
        if key == "id":
            stmt = stmt.where(Metric.id == UUID(str(value)))
        elif key in ("experiment_id", "experimentId"):
            stmt = stmt.where(Metric.experiment_id == UUID(str(value)))
        elif key == "parent_type":
            stmt = stmt.where(Metric.parent_type == value)
        elif key == "parent_id":
            stmt = stmt.where(Metric.parent_id == UUID(str(value)))
        elif key == "name":
            stmt = stmt.where(Metric.name == value)
        elif key == "kind":
            stmt = stmt.where(Metric.kind == value)
        elif key == "type":
            stmt = stmt.where(Metric.type == value)
        elif key == "semantic_type":
            stmt = stmt.where(Metric.semantic_type == value)
        elif key in ("produced_by_task", "producedByTask"):
            stmt = stmt.where(Metric.produced_by_task == value)
        elif key == "metadata" and isinstance(value, dict):
            stmt = stmt.where(Metric.metric_metadata.contains(value))
        else:
            continue

    result = await db.execute(stmt)
    metrics = result.scalars().all()
    return [MetricRead.model_validate(orm_columns_dict(m)) for m in metrics]

