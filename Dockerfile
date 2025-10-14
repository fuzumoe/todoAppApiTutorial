FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app 

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --upgrade pip && pip install uv

# --- if you have pyproject.toml (recommended)
COPY pyproject.toml ./ 

# install project dependencies
RUN uv pip install -e .[dev] --system || true

# copy source
COPY app ./app

# re-install in case editable needs sources (safe if already done)
RUN uv pip install -e . --system

EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
