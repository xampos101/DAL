"""Phase 4 query endpoints (legacy-style POST queries)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dal_service.db.session import get_db
from dal_service.deps import require_access_token
from dal_service.models.experiment import Experiment
from dal_service.models.workflow import Workflow
from dal_service.models.metrics import Metric
from dal_service.schemas.experiment import ExperimentRead
from dal_service.schemas.workflow import WorkflowRead
from dal_service.schemas.metric import MetricRead

router = APIRouter(tags=["queries"])


def _ensure_allowed_keys(filters: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(filters.keys()) - allowed)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported filter keys: {', '.join(unknown)}",
        )


@router.post("/experiments-query")
async def experiments_query(
    filters: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Legacy-style experiments query. Empty body returns all."""
    allowed = {
        "id",
        "name",
        "intent",
        "status",
        "model",
        "comment",
    }
    _ensure_allowed_keys(filters, allowed)

    stmt = select(Experiment)
    if "id" in filters:
        stmt = stmt.where(Experiment.id == UUID(str(filters["id"])))
    if "name" in filters:
        stmt = stmt.where(Experiment.name == filters["name"])
    if "intent" in filters:
        stmt = stmt.where(Experiment.intent == filters["intent"])
    if "status" in filters:
        stmt = stmt.where(Experiment.status == filters["status"])
    if "model" in filters:
        stmt = stmt.where(Experiment.model == filters["model"])
    if "comment" in filters:
        stmt = stmt.where(Experiment.comment == filters["comment"])

    result = await db.execute(stmt)
    experiments = result.scalars().all()
    return {"experiments": [ExperimentRead.model_validate(e) for e in experiments]}


@router.post("/workflows-query")
async def workflows_query(
    filters: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Legacy-style workflows query. Empty body returns all."""
    allowed = {
        "id",
        "experiment_id",
        "name",
        "status",
        "comment",
    }
    _ensure_allowed_keys(filters, allowed)

    stmt = select(Workflow)
    if "id" in filters:
        stmt = stmt.where(Workflow.id == UUID(str(filters["id"])))
    if "experiment_id" in filters:
        stmt = stmt.where(Workflow.experiment_id == UUID(str(filters["experiment_id"])))
    if "name" in filters:
        stmt = stmt.where(Workflow.name == filters["name"])
    if "status" in filters:
        stmt = stmt.where(Workflow.status == filters["status"])
    if "comment" in filters:
        stmt = stmt.where(Workflow.comment == filters["comment"])

    result = await db.execute(stmt)
    workflows = result.scalars().all()
    return {"workflows": [WorkflowRead.model_validate(w) for w in workflows]}


@router.post("/metrics-query")
async def metrics_query(
    filters: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Legacy-style metrics query. Empty body returns all."""
    allowed = {
        "id",
        "experiment_id",
        "parent_type",
        "parent_id",
        "name",
        "kind",
        "type",
        "semantic_type",
        "produced_by_task",
    }
    _ensure_allowed_keys(filters, allowed)

    stmt = select(Metric)
    if "id" in filters:
        stmt = stmt.where(Metric.id == UUID(str(filters["id"])))
    if "experiment_id" in filters:
        stmt = stmt.where(Metric.experiment_id == UUID(str(filters["experiment_id"])))
    if "parent_type" in filters:
        stmt = stmt.where(Metric.parent_type == filters["parent_type"])
    if "parent_id" in filters:
        stmt = stmt.where(Metric.parent_id == UUID(str(filters["parent_id"])))
    if "name" in filters:
        stmt = stmt.where(Metric.name == filters["name"])
    if "kind" in filters:
        stmt = stmt.where(Metric.kind == filters["kind"])
    if "type" in filters:
        stmt = stmt.where(Metric.type == filters["type"])
    if "semantic_type" in filters:
        stmt = stmt.where(Metric.semantic_type == filters["semantic_type"])
    if "produced_by_task" in filters:
        stmt = stmt.where(Metric.produced_by_task == filters["produced_by_task"])

    result = await db.execute(stmt)
    metrics = result.scalars().all()
    return {"metrics": [MetricRead.model_validate(m) for m in metrics]}

