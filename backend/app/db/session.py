"""Database engine and request-session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a transaction-capable session and always release its connection."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def database_is_available() -> bool:
    """Perform a minimal database connectivity check for readiness probes."""

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception:
        return False
    return True
