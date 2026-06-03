# Lantern OS Headless Restart Guide

What survives a restart, what doesn't, and how to make everything auto-start with zero frills.

---

## What Dies on Restart (unless configured)

| Component | Survives? | Why | Fix |
|-----------|-----------|-----|-----|
| CSF Python v0.7 | ❌ No | Manual script | Use Rust CSF container |
| CADD Python skill | ❌ No | Manual skill | Use Rust CADD container |
| MCP servers | ❌ No | IDE extension | Configure IDE auto-start |
| Docker containers | ⚠️ Sometimes | Docker Desktop setting | Enable "Start Docker Desktop on login" |
| Data in containers | ❌ No | Containers are ephemeral | Mount host volumes |

## What Survives (if using this guide)

| Component | Survives? | How |
|-----------|-----------|-----|
| CSF Rust worker | ✅ Yes | Docker `restart: unless-stopped` + host volume |
| CADD Rust worker | ✅ Yes | Docker `restart: unless-stopped` + host volume |
| Caddy proxy | ✅ Yes | Docker `restart: unless-stopped` |
| Archives in `/data/archives` | ✅ Yes | Host bind mount |
| Brand assets in `/assets/brand` | ✅ Yes | Host bind mount |
| Git repo | ✅ Yes | Filesystem |

---

## Quick Start: One Command Restart

### Windows (PowerShell)

```powershell
.\scripts\restart-headless.ps1
```

### Linux/macOS (Bash)

```bash
./scripts/restart-headless.sh
```

Both scripts:
1. Check Docker is installed
2. Create data directories if missing
3. Build Rust CSF + CADD from source
4. Start all services with auto-restart
5. Run health checks
6. Print endpoints

---

## Manual Docker Commands

```bash
# Start everything
docker compose -f docker-compose.headless.yml up -d --build

# Check status
docker compose -f docker-compose.headless.yml ps

# View logs
docker compose -f docker-compose.headless.yml logs -f

# Stop everything
docker compose -f docker-compose.headless.yml down

# Stop and delete data volumes (DANGER)
docker compose -f docker-compose.headless.yml down -v
```

---

## Windows: Auto-Start on Login (No Docker)

If you don't want Docker, run the Rust binaries directly as Windows services.

### Step 1: Build Rust binaries

```powershell
cd src\csf_rust
cargo build --release
cd ..\cadd_rust
cargo build --release
```

### Step 2: Install as Windows Services

Use `nssm` (Non-Sucking Service Manager):

```powershell
# Download nssm from https://nssm.cc/
# Then:
nssm install LanternCSF "C:\path\to\lantern-os\src\csf_rust\target\release\csf.exe"
nssm set LanternCSF AppParameters "server --bind 0.0.0.0:9000 --data-dir C:\path\to\data\archives"
nssm set LanternCSF DisplayName "Lantern OS CSF Worker"
nssm set LanternCSF Start SERVICE_AUTO_START

nssm install LanternCADD "C:\path\to\lantern-os\src\cadd_rust\target\release\cadd.exe"
nssm set LanternCADD AppParameters "watch C:\path\to\assets\incoming --brand-dir C:\path\to\assets\brand"
nssm set LanternCADD DisplayName "Lantern OS CADD Worker"
nssm set LanternCADD Start SERVICE_AUTO_START

# Start services
net start LanternCSF
net start LanternCADD
```

---

## Linux: systemd Auto-Start

Create `/etc/systemd/system/lantern-csf.service`:

```ini
[Unit]
Description=Lantern OS CSF Worker
After=network.target

[Service]
Type=simple
ExecStart=/opt/lantern-os/csf server --bind 0.0.0.0:9000 --data-dir /var/lib/lantern/archives
Restart=always
RestartSec=5
User=lantern
Group=lantern

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/lantern-cadd.service`:

```ini
[Unit]
Description=Lantern OS CADD Worker
After=network.target

[Service]
Type=simple
ExecStart=/opt/lantern-os/cadd watch /var/lib/lantern/incoming --brand-dir /var/lib/lantern/brand
Restart=always
RestartSec=5
User=lantern
Group=lantern

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable lantern-csf lantern-cadd
sudo systemctl start lantern-csf lantern-cadd
```

---

## MCP Servers (separate concern)

MCP (Model Context Protocol) servers are managed by your IDE (Cursor, VS Code, Claude Desktop). They are **not** part of Lantern OS infrastructure.

| MCP Server | Survives Restart? | How to Auto-Start |
|------------|-------------------|-------------------|
| Cursor/VS Code built-in | ✅ Yes | IDE auto-starts them |
| Custom MCP (e.g., `mcp-server-fetch`) | ❌ No | Configure in IDE settings |

**To auto-start MCP:**
- VS Code: `.vscode/mcp.json` or settings.json
- Cursor: Settings → MCP → Add server → configure command
- Claude Desktop: `claude_desktop_config.json`

Example `.vscode/mcp.json`:

```json
{
  "servers": {
    "lantern-csf": {
      "command": "docker",
      "args": ["exec", "-i", "lantern-csf", "/app/csf", "mcp"]
    }
  }
}
```

---

## Troubleshooting

### "Docker not running"

Windows: Open Docker Desktop → Settings → General → "Start Docker Desktop when you log in"

### "Port already in use"

```bash
# Find what's using port 3000
lsof -i :3000
# or Windows:
netstat -ano | findstr :3000
```

### "CSF container won't start"

```bash
# Check logs
docker compose -f docker-compose.headless.yml logs lantern-csf
# Rebuild
docker compose -f docker-compose.headless.yml up -d --build --force-recreate csf-worker
```

### "Data disappeared after restart"

You probably didn't mount host volumes. Check `docker-compose.headless.yml` has:

```yaml
volumes:
  - ./data/archives:/data/archives
```

---

## Architecture

```
+-------------------------------------------------------------+
|                        Your Machine                         |
|  +----------------+  +----------------+  +----------------+ |
|  | lantern-csf    |  | lantern-cadd   |  | lantern-proxy  | |
|  | (Rust binary)  |  | (Rust binary)  |  | (Caddy)        | |
|  | Port 9000      |  | Watch dir      |  | Port 80/443    | |
|  | Auto-restart   |  | Auto-restart   |  | Auto-restart   | |
|  +----------------+  +----------------+  +----------------+ |
|         |                    |                    |           |
|  +-----------------------------------------------------+    |
|  |              Host volumes (survive restart)           |    |
|  |  ./data/archives   ./assets/brand   ./assets/incoming |    |
|  +-----------------------------------------------------+    |
+-------------------------------------------------------------+
```

No dashboard. No GUI. Just APIs, volumes, and auto-restart.
