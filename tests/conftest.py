"""Pytest configuration: test DB, dependency overrides, shared fixtures.

Set ACCESS_TOKEN and DATABASE_URL before importing dal_service so config and
optional global engine see test values. Override get_db to use the test
async_sessionmaker explicitly.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

# ---------------------------------------------------------------------------
# Environment — must run before any dal_service import that loads config/session
# ---------------------------------------------------------------------------
os.environ.setdefault("ACCESS_TOKEN", "test-token")
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/dal_test",
)

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dal_service.models import Base
from dal_service.models.experiment import Experiment  # noqa: F401 — register ORM
from dal_service.models.metrics import Metric, MetricAggregation, MetricRecord  # noqa: F401
from dal_service.models.workflow import Workflow  # noqa: F401

_test_engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)

TestingSessionLocal = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from dal_service.db.session import get_db  # noqa: E402
from dal_service.main import app  # noqa: E402

app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_schema() -> AsyncGenerator[None, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(prepare_schema) -> AsyncGenerator[None, None]:
    async with _test_engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE metric_records, metric_aggregations, metrics, workflows, "
                "experiments RESTART IDENTITY CASCADE"
            )
        )
    yield


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"access-token": "test-token"}


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def sample_experiment_id(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> str:
    response = await async_client.put(
        "/api/experiments",
        json={"name": "fixture-exp"},
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["message"]["experimentId"]


@pytest_asyncio.fixture
async def sample_workflow_id(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
) -> str:
    response = await async_client.put(
        "/api/workflows",
        json={"experiment_id": sample_experiment_id, "name": "fixture-wf"},
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["workflow_id"]


@pytest_asyncio.fixture
async def sample_metric_id(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_workflow_id: str,
) -> str:
    response = await async_client.put(
        "/api/metrics",
        json={
            "parent_type": "workflow",
            "parent_id": sample_workflow_id,
            "name": "fixture-metric",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["metric_id"]
