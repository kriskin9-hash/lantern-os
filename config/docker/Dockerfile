# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies only in builder stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy source code
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser apps/ apps/
COPY --chown=appuser:appuser services/ services/
COPY --chown=appuser:appuser scripts/ scripts/
COPY --chown=appuser:appuser data/ data/
COPY --chown=appuser:appuser config/docker/entrypoint.sh /app/entrypoint.sh

# Create working directories
RUN mkdir -p /app/{logs,config,state} && \
    chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PORT=5000

EXPOSE 5000 4177 8765 4178 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9000/health || exit 1

CMD ["/app/entrypoint.sh"]
