"""Contract / shape tests for Engine-compatible DAL responses."""

from __future__ import annotations

import uuid

import httpx
import pytest


@pytest.mark.asyncio
async def test_experiments_query_returns_bare_list(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.post(
        "/api/experiments-query",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == []


@pytest.mark.asyncio
async def test_executed_experiments_shape(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.get("/api/executed-experiments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "executed_experiments" in data
    assert isinstance(data["executed_experiments"], list)


@pytest.mark.asyncio
async def test_put_metrics_without_experiment_id_returns_201(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_workflow_id: str,
) -> None:
    response = await async_client.put(
        "/api/metrics",
        json={
            "parent_type": "workflow",
            "parent_id": sample_workflow_id,
            "name": "contract-metric",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert "metric_id" in body
    uuid.UUID(body["metric_id"])


@pytest.mark.asyncio
async def test_metrics_data_and_records_contract(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_metric_id: str,
) -> None:
    put_resp = await async_client.put(
        f"/api/metrics-data/{sample_metric_id}",
        json={"records": [{"value": 1.0}]},
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    put_body = put_resp.json()
    assert put_body == {"message": "ok", "inserted": 1}

    get_resp = await async_client.get(
        f"/api/metrics/{sample_metric_id}/records",
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    get_body = get_resp.json()
    assert isinstance(get_body, dict)
    assert "records" in get_body
    assert isinstance(get_body["records"], list)
    assert len(get_body["records"]) >= 1
    assert float(get_body["records"][0]["value"]) == 1.0
