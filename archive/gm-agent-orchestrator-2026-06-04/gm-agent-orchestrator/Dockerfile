FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create local storage directories
RUN mkdir -p ~/.lantern/telemetry ~/.lantern/state ~/.lantern/sounds ~/.bettersafe ~/.lantern/rag-knowledge-base

# Expose ports (if needed for dashboard)
EXPOSE 8766

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LANTERN_MODE=local
ENV RAG_STORAGE=local

# Entrypoint: Start Lantern + BetterSafe + RAG + Autopilot
CMD ["python3", "scripts/lantern_orchestrator_main.py"]
