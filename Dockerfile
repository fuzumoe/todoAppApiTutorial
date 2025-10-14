# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app 

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# --- if you have pyproject.toml (recommended)
COPY pyproject.toml ./
# optional: copy lockfile if you have it
# COPY uv.lock ./
RUN pip install --upgrade pip && pip install hatchling uv
# install project (no sources yet -> deps only)
RUN uv pip install -e .[dev] --system || true

# copy source
COPY app ./app

# re-install in case editable needs sources (safe if already done)
RUN uv pip install -e . --system

EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
