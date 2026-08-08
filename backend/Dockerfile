# ── Build stage: install dependencies ────────────────────────────────────────
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (maximises layer caching)
COPY pyproject.toml uv.lock .python-version ./

# Install dependencies into /app/.venv
RUN uv sync --frozen --no-install-project --no-dev

# ── Runtime stage: minimal production image ──────────────────────────────────
FROM python:3.14-slim

# Non-root user for security (EKS best practice)
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --no-create-home appuser \
    && mkdir -p /tmp/pcs/uploads /tmp/pcs/downloads \
    && chown -R appuser:appuser /tmp/pcs

WORKDIR /app

# Copy venv from builder (same base image = compatible binaries)
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/
COPY config/ ./config/

# Set venv on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
