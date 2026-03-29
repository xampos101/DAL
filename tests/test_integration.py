"""End-to-end flows across experiments, workflows, and metrics."""

from __future__ import annotations

import uuid

import httpx
import pytest


@pytest.mark.asyncio
async def test_create_experiment_get_verify_fields(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    create = await async_client.put(
        "/api/experiments",
        json={"name": "integration-exp", "intent": "test", "status": "new"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    exp_id = create.json()["message"]["experimentId"]
    uuid.UUID(exp_id)

    get_resp = await async_client.get(f"/api/experiments/{exp_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    exp = get_resp.json()["experiment"]
    assert exp["id"] == exp_id
    assert exp["name"] == "integration-exp"
    assert exp["intent"] == "test"
    assert exp["workflow_ids"] == []


@pytest.mark.asyncio
async def test_create_workflow_get_verify_experiment_id(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    create_exp = await async_client.put(
        "/api/experiments",
        json={"name": "parent-exp"},
        headers=auth_headers,
    )
    exp_id = create_exp.json()["message"]["experimentId"]

    wf_resp = await async_client.put(
        "/api/workflows",
        json={"experiment_id": exp_id, "name": "child-wf"},
        headers=auth_headers,
    )
    assert wf_resp.status_code == 201
    wf_id = wf_resp.json()["workflow_id"]

    get_wf = await async_client.get(f"/api/workflows/{wf_id}", headers=auth_headers)
    assert get_wf.status_code == 200
    wf = get_wf.json()["workflow"]
    assert wf["experiment_id"] == exp_id
    assert wf["name"] == "child-wf"


@pytest.mark.asyncio
async def test_metric_without_experiment_id_ingest_and_read_records(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    exp_id = (
        await async_client.put("/api/experiments", json={"name": "m-exp"}, headers=auth_headers)
    ).json()["message"]["experimentId"]
    wf_id = (
        await async_client.put(
            "/api/workflows",
            json={"experiment_id": exp_id, "name": "m-wf"},
            headers=auth_headers,
        )
    ).json()["workflow_id"]

    m_resp = await async_client.put(
        "/api/metrics",
        json={
            "parent_type": "workflow",
            "parent_id": wf_id,
            "name": "series-a",
            "kind": "series",
        },
        headers=auth_headers,
    )
    assert m_resp.status_code == 201
    metric_id = m_resp.json()["metric_id"]

    data_resp = await async_client.put(
        f"/api/metrics-data/{metric_id}",
        json={"records": [{"value": 0.11}, {"value": 0.22}]},
        headers=auth_headers,
    )
    assert data_resp.status_code == 200
    assert data_resp.json()["inserted"] == 2

    rec_resp = await async_client.get(f"/api/metrics/{metric_id}/records", headers=auth_headers)
    assert rec_resp.status_code == 200
    records = rec_resp.json()["records"]
    values = sorted(float(r["value"]) for r in records)
    assert values == [0.11, 0.22]
