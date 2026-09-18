"""FastAPI application entry point and cross-cutting middleware."""

import logging
from collections.abc import Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.errors import validation_exception_handler
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_context
from app.core.readiness import dependency_status

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach or create a request ID for clients, logs, and error responses."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        token = request_id_context.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_context.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response


def create_app(dependency_checker: Callable[[], dict[str, bool]] = dependency_status) -> FastAPI:
    """Create the API application without connecting to external services."""

    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
    )
    app.state.dependency_checker = dependency_checker
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(health_router)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    logger.info("application_created", extra={"environment": settings.app_env})
    return app


app = create_app()
