"""Access-token header behaviour on protected routes."""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_missing_access_token_returns_401(async_client: httpx.AsyncClient) -> None:
    response = await async_client.get("/api/experiments")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wrong_access_token_returns_401(async_client: httpx.AsyncClient) -> None:
    response = await async_client.get(
        "/api/experiments",
        headers={"access-token": "wrong-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_correct_access_token_not_401(
    async_client: httpx.AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await async_client.get("/api/experiments", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "experiments" in body
