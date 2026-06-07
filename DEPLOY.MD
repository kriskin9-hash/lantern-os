# Lantern OS Deployment Guide

## Overview

Lantern OS deploys through **two lanes**:

| Lane | Target | Use Case |
|------|--------|----------|
| **GitHub Pages** | Static `gh-pages` branch | Public-facing Dream Journal UI (no backend required) |
| **Cloud Runtime** | Railway / AWS / Docker | Full chat + API backend |

The canonical local surface runs at `http://127.0.0.1:4177`.

---

## GitHub Pages Deploy (Static)

Triggered automatically on every push to `master` via `.github/workflows/deploy.yml`.

### What deploys
- `apps/lantern-garage/public/` → served at `https://alex-place.github.io/lantern-os/dream/`
- Root redirect → `/lantern-os/dream/`

### Manual trigger
```bash
gh workflow run deploy
```

### Verify
```bash
curl -sfL "https://alex-place.github.io/lantern-os/dream/" -o /dev/null -w "%{http_code}\n"
```

### Cold start
GitHub Pages has **no cold start**. Static assets are CDN-cached globally. First visit after a deploy may take 2-5s while cache invalidates.

---

## Cloud Runtime Deploy (Backend)

### Prerequisites
- Node.js >= 20
- At least one AI provider key (Gemini, Anthropic, OpenAI, xAI, or Ollama)

### Local start
```bash
cd apps/lantern-garage
npm install
npm run start       # port 4177
npm run start:cloud # port 8080, 0.0.0.0
npm run dev         # hot reload via node --watch
```

### Docker
```bash
cd apps/lantern-garage
docker build -t lantern-os .
docker run -p 8080:8080 -e GEMINI_API_KEY="..." lantern-os
```

### Railway
1. Connect repo at https://railway.app
2. Set `NIXPACKS_NODE_VERSION=20`
3. Add env vars: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
4. Deploys auto-trigger on `master` push

### AWS ECS
See `archive/aws-deployment/AWS-DEPLOYMENT-GUIDE.md` for full CloudFormation stack.

---

## Restart

### Local
```bash
# Find and kill existing
Get-NetTCPConnection -LocalPort 4177 | Select-Object OwningProcess
Stop-Process -Id <PID>

# Restart
npm run start
```

### Docker
```bash
docker restart <container_id>
```

### systemd (Linux server)
```bash
sudo systemctl restart lantern-os
```

### Cloud (Railway)
- Dashboard → Deploy → Redeploy latest commit
- Or push any commit to `master`

---

## Cold Start Behavior

| Target | Cold Start | Notes |
|--------|-----------|-------|
| GitHub Pages | None | Static CDN, instant |
| Local Node | ~2s | Module load, env parse, route mount |
| Docker | ~5s | Image startup + Node boot |
| Railway | ~10-30s | Container spin-up if auto-stop enabled |
| AWS ECS Fargate | ~30-60s | Task provisioning |

### Mitigating cold starts
- Keep `min_machines_running = 1` on Railway
- AWS ECS: use Fargate Spot with warm pool

---

## Health Checks

```bash
# Local
curl http://127.0.0.1:4177/api/health

# GitHub Pages
curl https://alex-place.github.io/lantern-os/dream/version.json

# Cloud
curl https://<your-cloud-url>/api/health
```

### Expected response
```json
{"status":"ok","version":"1.1.0","providerCount":3}
```

---

## Rollback

### GitHub Pages
```bash
git log --oneline origin/gh-pages -5
# Pick a previous deploy commit
git push origin <commit>:gh-pages --force
```

### Cloud
Railway: dashboard → previous deploy → rollback

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional* | Google Gemini API key |
| `ANTHROPIC_API_KEY` | Optional* | Claude API key |
| `OPENAI_API_KEY` | Optional* | OpenAI API key |
| `XAI_API_KEY` | Optional* | Grok API key |
| `OLLAMA_HOST` | Optional* | Local Ollama endpoint |
| `PORT` | No | Server port (default: 4177 local, 8080 cloud) |
| `LANTERN_REPO_ROOT` | No | Override repo root path |

*At least one provider key required for AI chat. Static site works without any.

---

## Troubleshooting

See `ISSUES.md` for common problems and fixes.
