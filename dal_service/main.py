"""FastAPI application entrypoint."""
from fastapi import FastAPI

from dal_service.routers import health
from dal_service.routers import experiments
from dal_service.routers import workflows
from dal_service.routers import metrics
from dal_service.routers import queries

app = FastAPI(title="ExtremeXP DAL", version="0.1.0")
app.include_router(health.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
