"""Dependency readiness checks kept separate from HTTP routing."""

from collections.abc import Callable

from redis import Redis

from app.core.config import get_settings
from app.db.session import database_is_available


def redis_is_available() -> bool:
    """Perform a minimal Redis ping for readiness probes."""

    try:
        return bool(Redis.from_url(get_settings().redis_url, socket_connect_timeout=1).ping())
    except Exception:
        return False


def dependency_status(
    database_check: Callable[[], bool] = database_is_available,
    redis_check: Callable[[], bool] = redis_is_available,
) -> dict[str, bool]:
    """Return named dependency status without raising probe failures."""

    return {"database": database_check(), "redis": redis_check()}
