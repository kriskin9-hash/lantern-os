FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/superfleet-memory /app/apps/superfleet-memory
COPY services/audit-verification-api /app/services/audit-verification-api

# Expose port
EXPOSE 8766

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "services.audit-verification-api.main:app", "--host", "0.0.0.0", "--port", "8766"]
