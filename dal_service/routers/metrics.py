"""Metrics API router: create, read, update, records."""

from __future__ import annotations

from uuid import UUID
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dal_service.db.session import get_db
from dal_service.deps import require_access_token
from dal_service.models.metrics import Metric, MetricRecord
from dal_service.models.workflow import Workflow
from dal_service.schemas.metric import (
    MetricCreate,
    MetricRead,
    MetricUpdate,
    MetricRecordRead,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])
metrics_data_router = APIRouter(tags=["metrics"])


@router.put("", status_code=201)
async def create_metric(
    body: MetricCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Create a new metric. Returns 201 with metric_id."""
    attrs = body.model_dump(exclude_unset=True)

    # Engine omits `experiment_id` when creating a metric.
    # We derive it from `parent_type`/`parent_id` for compatibility.
    resolved_experiment_id = attrs.get("experiment_id")
    if resolved_experiment_id is None:
        if body.parent_type == "workflow":
            workflow_result = await db.execute(
                select(Workflow).where(Workflow.id == body.parent_id)
            )
            workflow = workflow_result.scalars().one_or_none()
            if workflow is None or workflow.experiment_id is None:
                raise HTTPException(status_code=422, detail="Could not resolve experiment_id from workflow")
            resolved_experiment_id = workflow.experiment_id
        elif body.parent_type == "experiment":
            resolved_experiment_id = body.parent_id
        else:
            raise HTTPException(status_code=422, detail="Unsupported parent_type")

    # Ensure ORM constructor always receives a non-null `experiment_id`.
    attrs["experiment_id"] = resolved_experiment_id

    raw_metadata = attrs.pop("metadata", None) or {}
    attrs["metric_metadata"] = raw_metadata
    metric = Metric(**attrs)
    db.add(metric)
    await db.flush()
    await db.refresh(metric)
    return {"metric_id": str(metric.id)}


@router.get("/{metric_id}")
async def get_metric(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Get a single metric by id. 404 if not found."""
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalars().one_or_none()
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    return {"metric": MetricRead.model_validate(metric)}


@router.post("/{metric_id}")
async def update_metric(
    metric_id: UUID,
    body: MetricUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Partially update a metric. 404 if not found."""
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalars().one_or_none()
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    attrs = body.model_dump(exclude_unset=True)
    for key, value in attrs.items():
        if key == "metadata":
            setattr(metric, "metric_metadata", value)
        else:
            setattr(metric, key, value)
    await db.flush()
    await db.refresh(metric)
    return {"message": "Metric updated", "metric": MetricRead.model_validate(metric)}


@router.get("/{metric_id}/records")
async def get_metric_records(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Return normalized records for a metric from metric_records table."""
    result = await db.execute(select(MetricRecord).where(MetricRecord.metric_id == metric_id))
    records = result.scalars().all()
    return {"records": [MetricRecordRead.model_validate(r) for r in records]}


@metrics_data_router.put("/metrics-data/{metric_id}")
async def put_metric_data(
    metric_id: UUID,
    body: dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Engine-compatible endpoint for sending metric series data.

    Expected payload: { "records": [ { "value": <number> }, ... ] }
    """
    metric_result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = metric_result.scalars().one_or_none()
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    raw_records = body.get("records", [])
    if raw_records is None:
        raw_records = []
    if not isinstance(raw_records, list):
        raise HTTPException(status_code=422, detail="records must be a list")

    inserted = 0
    for item in raw_records:
        if not isinstance(item, dict) or "value" not in item:
            raise HTTPException(status_code=422, detail="Each record must be an object with a value")
        try:
            value = float(item["value"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="record.value must be a number") from exc
        record = MetricRecord(metric_id=metric_id, value=value)
        db.add(record)
        inserted += 1

    # Flush so records are persisted within this request.
    await db.flush()
    return {"message": "ok", "inserted": inserted}

