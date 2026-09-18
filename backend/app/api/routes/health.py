"""Liveness and dependency-readiness endpoints."""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="API liveness")
async def health() -> dict[str, str]:
    """Confirm that the API process can receive requests.

    Dependency checks deliberately belong to `/ready`, introduced in Phase 3.
    """

    return {"status": "ok"}


@router.get("/ready", summary="Dependency readiness")
async def ready(request: Request) -> JSONResponse:
    """Confirm required serving dependencies are available.

    The checker is injected at app creation so tests do not need a running database or Redis.
    """

    checker = request.app.state.dependency_checker
    dependencies = checker()
    is_ready = all(dependencies.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ready" if is_ready else "not_ready", "dependencies": dependencies},
    )
