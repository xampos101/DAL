"""Workflows API router: create, read, update."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dal_service.db.session import get_db
from dal_service.deps import require_access_token
from dal_service.utils.orm_columns import orm_columns_dict
from dal_service.models.experiment import Experiment
from dal_service.models.workflow import Workflow
from dal_service.models.metrics import Metric
from dal_service.schemas.workflow import WorkflowCreate, WorkflowRead, WorkflowUpdate
from dal_service.schemas.metric import MetricRead

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.put("", status_code=201)
async def create_workflow(
    body: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Create a new workflow linked to an experiment. Appends workflow id to experiment.workflow_ids. 404 if experiment not found."""
    result = await db.execute(select(Experiment).where(Experiment.id == body.experiment_id))
    experiment = result.scalars().one_or_none()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    attrs = body.model_dump(exclude_unset=True)
    # Ensure JSONB/array defaults for optional fields
    if "parameters" not in attrs or attrs["parameters"] is None:
        attrs["parameters"] = []
    if "tasks" not in attrs or attrs["tasks"] is None:
        attrs["tasks"] = []
    if "input_datasets" not in attrs or attrs["input_datasets"] is None:
        attrs["input_datasets"] = []
    if "output_datasets" not in attrs or attrs["output_datasets"] is None:
        attrs["output_datasets"] = []
    # Map public schema field `metadata` to ORM attribute `workflow_metadata`
    raw_metadata = attrs.pop("workflow_metadata", None)
    if raw_metadata is None:
        raw_metadata = {}
    attrs["workflow_metadata"] = raw_metadata
    if "metric_ids" not in attrs or attrs["metric_ids"] is None:
        attrs["metric_ids"] = []
    if "metrics" not in attrs or attrs["metrics"] is None:
        attrs["metrics"] = []
    workflow = Workflow(**attrs)
    db.add(workflow)
    await db.flush()
    # Append new workflow id to parent experiment's workflow_ids
    experiment.workflow_ids = list(experiment.workflow_ids or []) + [workflow.id]
    await db.flush()
    await db.refresh(workflow)
    return {"workflow_id": str(workflow.id)}


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Get a single workflow by id. 404 if not found."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalars().one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow": WorkflowRead.model_validate(orm_columns_dict(workflow))}


@router.post("/{workflow_id}")
async def update_workflow(
    workflow_id: UUID,
    body: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """Partially update a workflow. 404 if not found."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalars().one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    attrs = body.model_dump(exclude_unset=True)
    for key, value in attrs.items():
        if key == "workflow_metadata":
            setattr(workflow, "workflow_metadata", value)
        else:
            setattr(workflow, key, value)
    await db.flush()
    await db.refresh(workflow)
    return {
        "message": "Workflow updated",
        "workflow": WorkflowRead.model_validate(orm_columns_dict(workflow)),
    }


@router.get("/{workflow_id}/metrics")
async def list_workflow_metrics(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_access_token),
) -> dict:
    """List metrics attached to a specific workflow."""
    result = await db.execute(
        select(Metric).where(Metric.parent_type == "workflow", Metric.parent_id == workflow_id)
    )
    metrics = result.scalars().all()
    return {"metrics": [MetricRead.model_validate(orm_columns_dict(m)) for m in metrics]}
