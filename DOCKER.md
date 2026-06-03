# Docker — Lantern OS

**Current State (2026-06-03)**

This document reflects the actual Docker setup in the repository.

## Current Docker Files

| File | Purpose | Status |
|------|---------|--------|
| `apps/lantern-garage/Dockerfile` | Lantern Garage web service | Recommended for V1 |
| `Dockerfile.unified` | Heavy all-in-one image | Legacy / bloated |
| `Dockerfile.agent-launcher` | Agent launcher | Niche |
| `Dockerfile.dream-journal` | Dream Journal service | Niche |
| Multiple files in `ops/`, `services/`, `src/` | Various services | High sprawl |

## Recommendation (Compacted State)

### For Dream Journal V1.0.0
- Use **one container** only: `apps/lantern-garage/Dockerfile`
- Dream Journal chat + streaming runs inside Lantern Garage
- No need for separate Dream Journal container in V1
- Redis is **not required** for basic V1 chat + provider streaming
- Avoid the heavy `Dockerfile.unified` and scattered Dockerfiles in `ops/` and `services/`

### Future Direction (CSF-like Compaction)
- Reduce to **one Dockerfile per major service**
- Move all Docker-related files into a `docker/` directory
- Remove or archive legacy Dockerfiles (`ops/`, `services/`, old variants)
- Standardize on `docker-compose.yml` + override files only

## Quick Commands

```bash
# Build Lantern Garage
docker build -f apps/lantern-garage/Dockerfile -t lantern-garage:latest .

# Run locally
docker run -p 4177:8080 lantern-garage:latest
```

## Next Compaction Steps
- Audit and delete unused Dockerfiles
- Consolidate docker-compose files
- Update `CLEANUP.md` with Docker reduction progress

---
**Last Updated:** 2026-06-03