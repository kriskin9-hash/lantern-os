# MCP Delegation Service - Real-time Dashboard
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy service files
COPY services/mcp-delegation/ /app/
RUN chmod +x /app/dashboard.py /app/delegation.py

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 5100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:5100/ || exit 1

CMD ["python", "dashboard.py"]
