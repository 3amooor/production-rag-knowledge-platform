FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install ".[dev]"

FROM base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
RUN pip uninstall -y pytest pytest-asyncio ruff
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
