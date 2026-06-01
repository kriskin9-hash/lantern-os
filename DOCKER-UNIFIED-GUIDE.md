# Unified Lantern OS + HFF Convergence Container

**Status**: Ready for Production  
**Version**: 1.0.0-unified  
**Generated**: 2025

## Overview

This unified Docker setup combines all repositories into a single, modernized container:

- ✅ **lantern-os** — Control plane + dashboard
- ✅ **hff-lantern-recovery** — HFF API + apps
- ✅ **hff-master-clean** — Clean baseline
- ✅ **lantern-symbolic-sandbox** — Symbolic reasoning (optional)
- ✅ **hff-seven-validate** — Validation layer (optional)

**Key improvements**:
- Multi-stage Docker build (smaller final image)
- Python 3.12 + Node.js 22 (latest stable versions)
- Modernized dependencies (Flask 3.0, cryptography 41.0, etc.)
- Orchestrated services (Flask, Node.js, Discord bot, health endpoint)
- Optional Redis cache + PostgreSQL database
- Prometheus metrics collection
- Full health checks and monitoring

---

## Quick Start

### 1. Build the Unified Image

```bash
# Build locally
docker build \
  -f lantern-os/Dockerfile.unified \
  -t lantern-convergence:1.0.0-unified \
  .

# Or use docker-compose
docker-compose -f docker-compose.unified.yml build
```

### 2. Run with Docker Compose

```bash
# Start all services (app + cache + DB + metrics)
docker-compose -f docker-compose.unified.yml up -d

# View logs
docker-compose -f docker-compose.unified.yml logs -f lantern-convergence

# Stop services
docker-compose -f docker-compose.unified.yml down

# Clean up (remove volumes)
docker-compose -f docker-compose.unified.yml down -v
```

### 3. Run Standalone Container

```bash
docker run -d \
  --name lantern-convergence \
  -p 5000:5000 \
  -p 4177:4177 \
  -p 8765:8765 \
  -p 9000:9000 \
  -v lantern-data:/app/data \
  -e FLASK_ENV=production \
  lantern-convergence:1.0.0-unified
```

---

## Service Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| HFF Flask API | 5000 | `http://localhost:5000` | Main REST API |
| Lantern Dashboard | 4177 | `http://localhost:4177` | OS control plane |
| Lantern Browser | 8765 | `http://localhost:8765` | Browser interface |
| Discord Bot | 4178 | Internal | Discord integration |
| Health Endpoint | 9000 | `http://localhost:9000/health` | Health checks |
| Redis Cache | 6379 | Internal | Caching layer |
| PostgreSQL | 5432 | Internal | Persistent DB |
| Prometheus Metrics | 9090 | `http://localhost:9090` | Monitoring |

---

## Environment Variables

### Essential (Production)

```env
# Flask/Python
FLASK_ENV=production
PYTHONUNBUFFERED=1
PORT=5000

# Lantern
LANTERN_MODE=convergence-unified
LANTERN_DASHBOARD_PORT=4177

# Security
DEBUG=false
ALLOW_PUBLIC_WRITES=false
```

### Optional (API Keys)

```env
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
DISCORD_BOT_TOKEN=...
```

### Performance Tuning

```env
WORKERS=4              # Gunicorn workers
THREADS=2              # Threads per worker
TIMEOUT=120            # Request timeout (seconds)
```

---

## File Structure

```
lantern-os/
├── Dockerfile.unified          ← Main unified image
├── requirements.txt.unified    ← All dependencies (Python 3.12+)
├── .dockerignore               ← Build ignore patterns
├── ops/
│   ├── entrypoint.sh          ← Service orchestrator
│   ├── prometheus.yml         ← Metrics config
│   ├── Dockerfile-*           ← Legacy service images
│   └── ...
├── apps/
│   ├── lantern-garage/        ← Node.js dashboard
│   ├── lantern-browser/       ← Browser interface
│   └── rhythm-os/             ← Audio services
├── src/
│   └── discord_lounge_bot/    ← Discord bot
├── data/
│   ├── rag-house/             ← RAG memory store
│   ├── wallet/                ← Wallet data
│   └── media/                 ← Media library
└── docs/                       ← Documentation

hff-lantern-recovery/          ← Integrated into unified
hff-master-clean/              ← Integrated into unified
docker-compose.unified.yml     ← Multi-service orchestration
```

---

## Health Checks

### Unified Health Endpoint

```bash
# Check overall health
curl http://localhost:9000/health

# Response (example):
{
  "status": "healthy",
  "services": {
    "hff-api": true,
    "lantern-dashboard": true,
    "lantern-browser": true,
    "discord-bot": false
  },
  "mode": "convergence-unified"
}
```

### Individual Service Health

```bash
# HFF API
curl http://localhost:5000/health

# Lantern Dashboard
curl http://localhost:4177/api/health

# PostgreSQL (if running)
docker-compose exec lantern-db pg_isready -U lantern

# Redis (if running)
docker-compose exec lantern-cache redis-cli ping
```

---

## Logging

Logs are collected in `/app/logs/` inside the container:

```bash
# View logs from running container
docker exec lantern-convergence tail -f /app/logs/entrypoint.log
docker exec lantern-convergence tail -f /app/logs/hff-access.log
docker exec lantern-convergence tail -f /app/logs/hff-error.log

# Or via docker-compose
docker-compose -f docker-compose.unified.yml logs lantern-convergence
```

Log files:
- `entrypoint.log` — Service startup/orchestration
- `hff-access.log` — HFF API access logs
- `hff-error.log` — HFF API errors
- `browser-access.log` — Browser service logs
- `browser-error.log` — Browser service errors

---

## Persistent Data

Volumes (automatically created):

| Volume | Path | Purpose |
|--------|------|---------|
| `lantern-data` | `/app/data` | General data |
| `rag-house` | `/app/data/rag-house` | RAG memory |
| `wallet-data` | `/app/data/wallet` | Wallet schemas |
| `lantern-audio` | `/app/.lantern/sounds` | Audio library |
| `lantern-logs` | `/app/logs` | Service logs |
| `cache-data` | `/data` (Redis) | Cache storage |
| `db-data` | `/var/lib/postgresql/data` | Database |

### Backup Data

```bash
# Backup all volumes
docker run --rm \
  -v lantern-data:/data \
  -v $(pwd)/backup:/backup \
  busybox tar czf /backup/lantern-data.tar.gz /data

# Restore volumes
docker run --rm \
  -v lantern-data:/data \
  -v $(pwd)/backup:/backup \
  busybox tar xzf /backup/lantern-data.tar.gz -C /
```

---

## Security Best Practices

### 1. Environment Variables

```bash
# Use .env file (not committed to git)
echo ".env" >> .gitignore

# Create .env with secrets
cat > .env << EOF
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
DISCORD_BOT_TOKEN=...
POSTGRES_PASSWORD=secure-password-here
EOF

# Load in docker-compose.yml
docker-compose --env-file .env -f docker-compose.unified.yml up
```

### 2. Network Isolation

Docker Compose creates an isolated network (`lantern-network`) by default. Services communicate internally only.

### 3. Resource Limits

The compose file includes CPU/memory limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

### 4. Non-root User

Container runs as `lantern` user (non-root) for security.

---

## Performance Tuning

### CPU/Memory Allocation

```yaml
# docker-compose.unified.yml
deploy:
  resources:
    limits:
      cpus: '4'           # Increase for more concurrency
      memory: 4G          # Increase for larger datasets
    reservations:
      cpus: '2'           # Minimum reserved
      memory: 2G
```

### Gunicorn Workers

```bash
# More workers = better throughput, more memory
WORKERS=8 docker-compose up

# Formula: (2 × CPU cores) + 1 is typical
# For 4 cores: 9 workers
```

### Database Connection Pool

```env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs lantern-convergence

# Rebuild image
docker-compose build --no-cache lantern-convergence

# Start with debug output
FLASK_DEBUG=1 docker-compose up
```

### Out of memory

```bash
# Increase memory limit
memory: 8G  # in docker-compose.yml

# Reduce Gunicorn workers
WORKERS=4 docker-compose up
```

### Port already in use

```bash
# Find process using port
lsof -i :5000

# Kill process or use different port
PORT=5001 docker-compose up
```

### Database connection issues

```bash
# Check database is running
docker-compose exec lantern-db psql -U lantern -d lantern-convergence

# View database logs
docker-compose logs lantern-db
```

---

## Monitoring & Metrics

### Prometheus Setup

Prometheus is available at `http://localhost:9090`

```bash
# Query metrics (examples)
curl "http://localhost:9090/api/v1/query?query=up"
curl "http://localhost:9090/api/v1/query?query=http_requests_total"
```

### Real-time Logs

```bash
# Stream logs from all services
docker-compose logs -f

# Follow specific service
docker-compose logs -f lantern-convergence
```

---

## Deployment Scenarios

### Local Development

```bash
docker-compose -f docker-compose.unified.yml up
```

### Production (Single Server)

```bash
# Build image
docker build -f lantern-os/Dockerfile.unified -t lantern:prod .

# Run with persistent volumes and resource limits
docker run -d \
  --name lantern-prod \
  --restart unless-stopped \
  -p 5000:5000 \
  -p 4177:4177 \
  -v lantern-data:/app/data \
  -e FLASK_ENV=production \
  lantern:prod
```

### Production (Kubernetes)

See `lantern-os/ops/k8s/` for Kubernetes manifests.

```bash
kubectl apply -f lantern-os/ops/k8s/
```

### Cloud Deployment (Render, Railway, etc.)

```bash
# Docker image must be available
docker tag lantern-convergence:1.0.0-unified myregistry/lantern:latest
docker push myregistry/lantern:latest

# Deploy via platform dashboard or CLI
render deploy --image myregistry/lantern:latest
```

---

## Upgrading Dependencies

### Update Python packages

```bash
# Rebuild with updated requirements
docker-compose build --no-cache lantern-convergence

# Or manually update
pip list --outdated
pip install --upgrade <package-name>
```

### Update Node.js packages

```bash
# In lantern-os/apps/lantern-garage/
npm audit
npm update
npm audit fix
```

---

## Clean Up

```bash
# Stop all services
docker-compose -f docker-compose.unified.yml down

# Remove volumes
docker-compose -f docker-compose.unified.yml down -v

# Remove image
docker rmi lantern-convergence:1.0.0-unified

# Prune unused resources
docker system prune -a
```

---

## Next Steps

1. ✅ Build and test locally: `docker-compose up`
2. ✅ Configure environment variables in `.env`
3. ✅ Set up persistent volume backups
4. ✅ Deploy to production environment
5. ✅ Monitor metrics and logs
6. ✅ Set up CI/CD pipeline for automated builds

---

## Support & References

- **Docker**: https://docs.docker.com
- **Docker Compose**: https://docs.docker.com/compose
- **Flask**: https://flask.palletsprojects.com
- **Node.js**: https://nodejs.org
- **Kubernetes**: https://kubernetes.io

**Questions?** Check logs or refer to service-specific documentation in `lantern-os/docs/`.
