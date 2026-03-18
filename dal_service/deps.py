"""Shared FastAPI dependencies (e.g. auth)."""
from fastapi import Header, HTTPException

from dal_service.core.config import ACCESS_TOKEN


async def require_access_token(
    access_token: str | None = Header(default=None, alias="access-token"),
) -> None:
    """Validate access-token header; raise 401 if missing or invalid."""
    if not access_token or access_token != ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing access-token")
