"""SQLAlchemy declarative base shared by all persistent models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base metadata imported by Alembic to manage schema migrations."""
