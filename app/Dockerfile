FROM python:3.12.14-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip wheel --wheel-dir /wheels .


FROM python:3.12.14-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="Hybrid Observability API" \
      org.opencontainers.image.description="Instrumented FastAPI workload for the Hybrid Observability Platform" \
      org.opencontainers.image.source="https://github.com/itamarsb/hybrid-observability-platform" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

WORKDIR /app

RUN groupadd --gid 10001 appgroup \
    && useradd \
        --uid 10001 \
        --gid appgroup \
        --no-create-home \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        appuser \
    && python -m venv /opt/venv

COPY --from=builder /wheels /wheels

RUN python -m pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=3s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; port = os.getenv('APP_PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health/live', timeout=2).read()"]

CMD ["sh", "-c", "exec uvicorn hybrid_observability.main:app --host \"$APP_HOST\" --port \"$APP_PORT\""]
