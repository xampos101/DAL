"""Health check endpoint (no auth required)."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return service status."""
    return {"status": "ok"}
