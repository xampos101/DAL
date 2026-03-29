"""Extra router coverage for pytest-cov >= 80% on dal_service.routers."""

from __future__ import annotations

import uuid

import httpx
import pytest


@pytest.mark.asyncio
async def test_health_ok(async_client: httpx.AsyncClient) -> None:
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_experiment_404(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    rid = str(uuid.uuid4())
    response = await async_client.get(f"/api/experiments/{rid}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_experiments(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
) -> None:
    response = await async_client.get("/api/experiments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "experiments" in data
    assert len(data["experiments"]) >= 1
    ids = {e["id"] for e in data["experiments"]}
    assert sample_experiment_id in ids


@pytest.mark.asyncio
async def test_update_experiment(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
) -> None:
    response = await async_client.post(
        f"/api/experiments/{sample_experiment_id}",
        json={"status": "running", "comment": "updated"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    exp = response.json()["experiment"]
    assert exp["status"] == "running"
    assert exp["comment"] == "updated"


@pytest.mark.asyncio
async def test_list_experiment_metrics(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
    sample_metric_id: str,
) -> None:
    response = await async_client.get(
        f"/api/experiments/{sample_experiment_id}/metrics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert any(m["id"] == sample_metric_id for m in metrics)

    filtered = await async_client.get(
        f"/api/experiments/{sample_experiment_id}/metrics",
        params={"parent_type": "workflow"},
        headers=auth_headers,
    )
    assert filtered.status_code == 200


@pytest.mark.asyncio
async def test_get_workflow_404(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    rid = str(uuid.uuid4())
    response = await async_client.get(f"/api/workflows/{rid}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_workflow(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_workflow_id: str,
) -> None:
    response = await async_client.post(
        f"/api/workflows/{sample_workflow_id}",
        json={"status": "running"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["workflow"]["status"] == "running"


@pytest.mark.asyncio
async def test_list_workflow_metrics(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_workflow_id: str,
    sample_metric_id: str,
) -> None:
    response = await async_client.get(
        f"/api/workflows/{sample_workflow_id}/metrics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert any(m["id"] == sample_metric_id for m in metrics)


@pytest.mark.asyncio
async def test_get_metric_and_update(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_metric_id: str,
) -> None:
    get_resp = await async_client.get(f"/api/metrics/{sample_metric_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["metric"]["name"] == "fixture-metric"

    post_resp = await async_client.post(
        f"/api/metrics/{sample_metric_id}",
        json={"semantic_type": "score"},
        headers=auth_headers,
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["metric"]["semantic_type"] == "score"


@pytest.mark.asyncio
async def test_get_metric_404(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    rid = str(uuid.uuid4())
    response = await async_client.get(f"/api/metrics/{rid}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_workflow_experiment_not_found(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.put(
        "/api/workflows",
        json={"experiment_id": str(uuid.uuid4()), "name": "orphan"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_metric_resolve_experiment_from_parent_experiment(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
) -> None:
    response = await async_client.put(
        "/api/metrics",
        json={
            "parent_type": "experiment",
            "parent_id": sample_experiment_id,
            "name": "exp-level",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_put_metrics_data_metric_not_found(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.put(
        f"/api/metrics-data/{uuid.uuid4()}",
        json={"records": [{"value": 1.0}]},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_metrics_data_invalid_records(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_metric_id: str,
) -> None:
    bad = await async_client.put(
        f"/api/metrics-data/{sample_metric_id}",
        json={"records": "not-a-list"},
        headers=auth_headers,
    )
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_workflows_query_and_metrics_query_filters(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
    sample_workflow_id: str,
    sample_metric_id: str,
) -> None:
    wf_q = await async_client.post(
        "/api/workflows-query",
        json={"experimentId": sample_experiment_id},
        headers=auth_headers,
    )
    assert wf_q.status_code == 200
    assert isinstance(wf_q.json(), list)

    mq = await async_client.post(
        "/api/metrics-query",
        json={"experiment_id": sample_experiment_id},
        headers=auth_headers,
    )
    assert mq.status_code == 200
    assert isinstance(mq.json(), list)

    mq2 = await async_client.post(
        "/api/metrics-query",
        json={"producedByTask": "nope"},
        headers=auth_headers,
    )
    assert mq2.status_code == 200


@pytest.mark.asyncio
async def test_update_experiment_404(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.post(
        f"/api/experiments/{uuid.uuid4()}",
        json={"name": "ghost"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_workflow_404(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.post(
        f"/api/workflows/{uuid.uuid4()}",
        json={"status": "failed"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_metric_404(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.post(
        f"/api/metrics/{uuid.uuid4()}",
        json={"name": "n"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_metric_unresolved_workflow(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.put(
        "/api/metrics",
        json={
            "parent_type": "workflow",
            "parent_id": str(uuid.uuid4()),
            "name": "orphan-m",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_experiments_query_creator_and_metadata_contains(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    await async_client.put(
        "/api/experiments",
        json={
            "name": "meta-exp",
            "creator": {"name": "alice"},
            "metadata": {"tier": "gold"},
        },
        headers=auth_headers,
    )
    by_creator = await async_client.post(
        "/api/experiments-query",
        json={"creator": {"name": "alice"}},
        headers=auth_headers,
    )
    assert by_creator.status_code == 200
    assert len(by_creator.json()) >= 1

    by_meta = await async_client.post(
        "/api/experiments-query",
        json={"metadata": {"tier": "gold"}},
        headers=auth_headers,
    )
    assert by_meta.status_code == 200
    assert len(by_meta.json()) >= 1


@pytest.mark.asyncio
async def test_workflows_query_metadata_contains(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
) -> None:
    wf_id = (
        await async_client.put(
            "/api/workflows",
            json={
                "experiment_id": sample_experiment_id,
                "name": "wf-meta",
                "metadata": {"env": "ci"},
            },
            headers=auth_headers,
        )
    ).json()["workflow_id"]
    response = await async_client.post(
        "/api/workflows-query",
        json={"metadata": {"env": "ci"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    rows = response.json()
    assert any(w["id"] == wf_id for w in rows)


@pytest.mark.asyncio
async def test_metrics_query_metadata_and_produced_by_task(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_workflow_id: str,
) -> None:
    mid = (
        await async_client.put(
            "/api/metrics",
            json={
                "parent_type": "workflow",
                "parent_id": sample_workflow_id,
                "name": "task-m",
                "producedByTask": "t1",
                "metadata": {"src": "unit"},
            },
            headers=auth_headers,
        )
    ).json()["metric_id"]
    mq = await async_client.post(
        "/api/metrics-query",
        json={"producedByTask": "t1"},
        headers=auth_headers,
    )
    assert mq.status_code == 200
    assert any(m["id"] == mid for m in mq.json())

    mq2 = await async_client.post(
        "/api/metrics-query",
        json={"metadata": {"src": "unit"}},
        headers=auth_headers,
    )
    assert mq2.status_code == 200
    assert any(m["id"] == mid for m in mq2.json())


@pytest.mark.asyncio
async def test_experiments_query_filters(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
) -> None:
    await async_client.post(
        f"/api/experiments/{sample_experiment_id}",
        json={
            "intent": "bench",
            "status": "running",
            "model": "dsl-v1",
            "comment": "note",
        },
        headers=auth_headers,
    )
    for body in (
        {"name": "fixture-exp"},
        {"id": sample_experiment_id},
        {"intent": "bench"},
        {"status": "running"},
        {"model": "dsl-v1"},
        {"comment": "note"},
        {"unknown_key": "ignored"},
    ):
        response = await async_client.post(
            "/api/experiments-query",
            json=body,
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_workflows_query_id_name_status_comment(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
    sample_workflow_id: str,
) -> None:
    await async_client.post(
        f"/api/workflows/{sample_workflow_id}",
        json={"status": "scheduled", "comment": "wf-note"},
        headers=auth_headers,
    )
    wf = (await async_client.get(f"/api/workflows/{sample_workflow_id}", headers=auth_headers)).json()[
        "workflow"
    ]
    for body in (
        {"id": sample_workflow_id},
        {"experiment_id": sample_experiment_id},
        {"name": wf["name"]},
        {"status": "scheduled"},
        {"comment": "wf-note"},
    ):
        response = await async_client.post(
            "/api/workflows-query",
            json=body,
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_metrics_query_remaining_filters(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
    sample_experiment_id: str,
    sample_workflow_id: str,
    sample_metric_id: str,
) -> None:
    await async_client.post(
        f"/api/metrics/{sample_metric_id}",
        json={
            "kind": "scalar",
            "type": "float",
            "semantic_type": "accuracy",
        },
        headers=auth_headers,
    )
    for body in (
        {"id": sample_metric_id},
        {"experiment_id": sample_experiment_id},
        {"experimentId": sample_experiment_id},
        {"parent_id": sample_workflow_id},
        {"parent_type": "workflow"},
        {"name": "fixture-metric"},
        {"kind": "scalar"},
        {"type": "float"},
        {"semantic_type": "accuracy"},
    ):
        response = await async_client.post(
            "/api/metrics-query",
            json=body,
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert any(m["id"] == sample_metric_id for m in response.json())
