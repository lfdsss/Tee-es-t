# StudentFlow — production image
# ---------------------------------------------------------------------------
# Multi-stage build: install deps in a builder layer, copy the wheel into a
# slim runtime. Works on Railway, Fly.io, Render, Cloud Run, and any host
# that accepts a standard Docker image.

FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# System build deps (kept minimal; httpx, pydantic, supabase are pure-wheel)
RUN apt-get update \
 && apt-get install --no-install-recommends -y build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --prefix=/install .

# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH"

# Non-root user for a tiny bit of extra hygiene
RUN useradd --system --uid 1000 studentflow

WORKDIR /app

COPY --from=builder /install /install
COPY src ./src
COPY schema.sql ./schema.sql

USER studentflow

EXPOSE 8000

# Default to the API. Override on Railway/Fly/Render with:
#   CMD ["python", "-m", "studentflow.cli", "run-agents"]
# to start a worker instead of the API.
CMD ["sh", "-c", "uvicorn studentflow.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
