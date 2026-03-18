"""Metrics API router: create, read, update, records."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dal_service.db.session import get_db
from dal_service.deps import require_access_token
from dal_service.models.metrics import Metric, MetricRecord
from dal_service.schemas.metric import (
    MetricCreate,
    MetricRead,
    MetricUpdate,
    MetricRecordRead,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.put("", status_code=201)
async def create_metric(
    body: MetricCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Create a new metric. Returns 201 with metric_id."""
    attrs = body.model_dump(exclude_unset=True)
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

