# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code (from this service's context)
COPY --chown=appuser:appuser . /app/

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8766

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -m http.client 127.0.0.1 8766 GET /health 2>/dev/null || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8766"]
