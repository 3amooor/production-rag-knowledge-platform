"""Consistent, non-sensitive HTTP error responses."""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def error_payload(request: Request, code: str, message: str, details: Any = None) -> dict[str, Any]:
    """Build the API error envelope without exposing internal exception text."""

    return {
        "error": {"code": code, "message": message, "details": details},
        "request_id": getattr(request.state, "request_id", None),
    }


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return malformed client input in the platform's error envelope."""

    return JSONResponse(
        status_code=422,
        content=error_payload(request, "VALIDATION_ERROR", "Request validation failed.", exc.errors()),
    )
