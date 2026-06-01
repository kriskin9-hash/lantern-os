# Lantern Unified — Single Monorepo, Single Docker Container

**Status:** Production-Ready  
**Version:** 1.0.0-unified  
**Last Updated:** 2026-06-01

Lantern Unified consolidates three repositories into a single monorepo with one Docker container:
- **lantern-os** — Desktop app, Dashboard, Browser interface
- **gm-agent-orchestrator** — Suzie agent orchestration and management
- **human-flourishing-frameworks** — Flask API, Discord bot, Vosk STT, voice curator

## Quick Start

### 1. Clone and Build

```bash
git clone https://github.com/alex-place/lantern-unified.git
cd lantern-unified

# Build Docker image
docker build -f config/docker/Dockerfile -t lantern-unified:latest .

# Or use docker-compose
docker-compose build
```

### 2. Run

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or standalone
docker run -d \
  --name lantern \
  -p 5000:5000 \
  -p 4177:4177 \
  -p 8765:8765 \
  -p 4178:4178 \
  -p 9000:9000 \
  -v lantern-data:/app/data \
  lantern-unified:latest
```

### 3. Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| Flask API | http://localhost:5000 | Main REST API |
| Dashboard | http://localhost:4177 | Control plane |
| Browser | http://localhost:8765 | Web interface |
| Discord Bot | Internal | Discord integration |
| Health | http://localhost:9000/health | Health checks |

## Directory Structure

```
lantern-unified/
├── src/
│   ├── hff-api/              # Flask backend (from HFF)
│   ├── lantern-voice/        # Vosk STT integration
│   ├── suzie-orchestrator/   # Agent management (from gm-agent-orchestrator)
│   └── discord-bot/          # Discord integration
├── apps/
│   ├── lantern-desktop/      # Desktop chat app
│   ├── lantern-browser/      # Browser interface
│   ├── lantern-garage/       # Dashboard
│   └── bettersafe/           # Safety monitoring
├── services/
│   ├── rag-house/            # Knowledge base
│   ├── wallet/               # Data storage
│   └── media-library/        # Public domain curator
├── scripts/
│   ├── orchestration/        # Agent and deployment scripts
│   ├── deployment/           # Cloud deployment
│   └── testing/              # Test utilities
├── config/
│   ├── docker/               # Docker build files
│   ├── kubernetes/           # K8s manifests
│   └── github/               # GitHub Actions
├── docs/                     # Documentation
├── tests/                    # Test suites
└── data/                     # Models, sounds, RAG data
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

Key variables:
- `ANTHROPIC_API_KEY` — Claude API access
- `OPENAI_API_KEY` — GPT access (optional)
- `DISCORD_BOT_TOKEN` — Discord bot token
- `FLASK_ENV` — `production` or `development`

### Docker Compose

Services included:
- **lantern-unified** — Main container
- **lantern-db** — PostgreSQL database (optional)
- **lantern-cache** — Redis cache (optional)

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run Flask app
cd src/hff-api && python app.py
```

### Testing

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/unit/test_api.py -v

# Run with coverage
pytest --cov=src tests/
```

### Building Scripts

```bash
# Run orchestration scripts
powershell scripts/orchestration/Start-ActiveAgentFleet.ps1

# Run deployment
powershell scripts/deployment/Deploy-DiscordBotCloud.ps1
```

## Architecture

### Container Flow

```
Docker Container (lantern-unified)
├── Flask API (port 5000)
│   ├── HFF auth & routes
│   ├── Agent management
│   └── Media curator API
├── Discord Bot (port 4178)
│   └── Status & commands
├── Dashboard (port 4177)
│   └── Web control panel
├── Browser (port 8765)
│   └── Chat interface
└── Health Endpoint (port 9000)
    └── Liveness probe
```

### Data Flow

```
User Input
  ↓
[Flask API] ← [Discord Bot] / [Browser] / [Dashboard]
  ↓
[SQLAlchemy/PostgreSQL] ← [Redis Cache]
  ↓
[AI Provider] (Claude/GPT)
  ↓
Response → User
```

## Deployment

### Render (Current)

```bash
# Deploy to Render
git push origin main
# Render auto-deploys on push
```

### Kubernetes

```bash
kubectl apply -f config/kubernetes/
kubectl get services
```

### Docker Hub

```bash
docker build -t your-username/lantern-unified:latest .
docker push your-username/lantern-unified:latest
```

## Scripts & Automation

All scripts consolidated in `scripts/`:

| Script | Purpose |
|--------|---------|
| Start-ActiveAgentFleet.ps1 | Launch agent fleet |
| Deploy-DiscordBotCloud.ps1 | Deploy Discord bot |
| Invoke-AutomationOrchestrator.ps1 | Run automation |
| Test-ConvergenceAgentFleet.py | Validate agents |

Run scripts from monorepo root:

```bash
powershell scripts/orchestration/Start-ActiveAgentFleet.ps1
python scripts/orchestration/Test-ConvergenceAgentFleet.py
```

## Monitoring & Logs

```bash
# View logs
docker-compose logs -f lantern-unified

# Check health
curl http://localhost:9000/health

# Database status
docker-compose exec lantern-db pg_isready -U lantern

# Cache status
docker-compose exec lantern-cache redis-cli ping
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs lantern-unified

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### Port already in use

```bash
# Find process
lsof -i :5000

# Use different port
PORT=5001 docker-compose up
```

### Database connection failed

```bash
# Check database is running
docker-compose ps

# Restart database
docker-compose restart lantern-db
```

## Contributing

1. Create a feature branch
2. Make changes
3. Test locally (`docker-compose up`)
4. Commit with clear message
5. Push and create PR

## License

See LICENSE file.

## Support

- **Issues**: GitHub Issues
- **Documentation**: `docs/` directory
- **API Docs**: `docs/api/`
- **Architecture**: `docs/architecture/`

## What's Included

✅ Lantern Desktop chat app  
✅ Lantern Browser interface  
✅ Lantern Dashboard control plane  
✅ Discord bot integration  
✅ Suzie agent orchestration (1–20+ agents)  
✅ Voice (Vosk STT)  
✅ Voice curator (public domain audio)  
✅ Flask REST API  
✅ PostgreSQL database  
✅ Redis cache  
✅ 135+ automation scripts  
✅ Docker & Kubernetes configs  
✅ GitHub Actions CI/CD  

## Next Steps

- [ ] Configure environment variables (`.env`)
- [ ] Build Docker image locally
- [ ] Test with docker-compose
- [ ] Review scripts in `scripts/orchestration/`
- [ ] Deploy to Render or self-hosted
- [ ] Set up monitoring and alerts

---

**Repository**: github.com/alex-place/lantern-unified  
**Last built**: $(date)  
**Status**: ✅ Ready for production
