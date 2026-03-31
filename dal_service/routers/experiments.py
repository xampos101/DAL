"""Experiments API router: create, read, update, list."""

from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dal_service.db.session import get_db
from dal_service.deps import require_access_token
from dal_service.utils.orm_columns import orm_columns_dict
from dal_service.models.experiment import Experiment
from dal_service.models.metrics import Metric
from dal_service.schemas.experiment import (
    ExperimentCreate,
    ExperimentListItem,
    ExperimentRead,
    ExperimentUpdate,
)
from dal_service.schemas.metric import MetricRead

router = APIRouter(prefix="/experiments", tags=["experiments"])
# Separate router (no /experiments prefix) for Engine legacy endpoints.
executed_router = APIRouter(tags=["experiments"])


@executed_router.get("/executed-experiments")
async def get_executed_experiments(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Engine-compatible endpoint returning { executed_experiments: [...] }."""
    result = await db.execute(select(Experiment).order_by(Experiment.created_at.desc()))
    experiments = result.scalars().all()
    return {
        "executed_experiments": [
            ExperimentRead.model_validate(orm_columns_dict(e)) for e in experiments
        ]
    }


@router.put("", status_code=201)
async def create_experiment(
    body: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Create a new experiment. Returns 201 with message.experimentId."""
    attrs = body.model_dump(exclude_unset=True)
    # Ensure defaults for required model fields
    if "status" not in attrs:
        attrs["status"] = "new"
    # Map public schema field `metadata` to ORM attribute `experiment_metadata`
    raw_metadata = attrs.pop("experiment_metadata", None)
    if raw_metadata is None:
        raw_metadata = {}
    attrs["experiment_metadata"] = raw_metadata
    if "creator" not in attrs or attrs["creator"] is None:
        attrs["creator"] = {}
    # workflow_ids default handled by model
    experiment = Experiment(**attrs)
    db.add(experiment)
    await db.flush()
    await db.refresh(experiment)
    return {"message": {"experimentId": str(experiment.id)}}


@router.get("")
async def list_experiments(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """List experiments ordered by created_at DESC. Returns { experiments: [...] }."""
    result = await db.execute(
        select(Experiment).order_by(Experiment.created_at.desc()).limit(limit).offset(offset)
    )
    experiments = result.scalars().all()
    return {
        "experiments": [ExperimentListItem.model_validate(orm_columns_dict(e)) for e in experiments]
    }


@router.get("/{experiment_id}")
async def get_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Get a single experiment by id. 404 if not found."""
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalars().one_or_none()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"experiment": ExperimentRead.model_validate(orm_columns_dict(experiment))}


@router.post("/{experiment_id}")
async def update_experiment(
    experiment_id: UUID,
    body: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Partially update an experiment. 404 if not found."""
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalars().one_or_none()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    attrs = body.model_dump(exclude_unset=True)
    for key, value in attrs.items():
        if key == "experiment_metadata":
            setattr(experiment, "experiment_metadata", value)
        else:
            setattr(experiment, key, value)
    await db.flush()
    await db.refresh(experiment)
    return {
        "message": "Experiment updated",
        "experiment": ExperimentRead.model_validate(orm_columns_dict(experiment)),
    }


@router.get("/{experiment_id}/metrics")
async def list_experiment_metrics(
    experiment_id: UUID,
    parent_type: Literal["experiment", "workflow"] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """List metrics for a given experiment, optionally filtered by parent_type."""
    stmt = select(Metric).where(Metric.experiment_id == experiment_id)
    if parent_type is not None:
        stmt = stmt.where(Metric.parent_type == parent_type)
    result = await db.execute(stmt)
    metrics = result.scalars().all()
    return {"metrics": [MetricRead.model_validate(orm_columns_dict(m)) for m in metrics]}
