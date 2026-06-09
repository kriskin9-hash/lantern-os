# Lantern OS / Dream Journal — Official Install Guide

> **Version:** pre-1.0.0  
> **Last updated:** 2026-06-03  
> **OS:** Windows 10/11 (PowerShell)  
> **Runtime:** Python 3.10+ with Ollama (local LLM)  

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (One-Click Installer)](#quick-start-one-click-installer)
3. [Manual Install](#manual-install)
4. [Ollama Model Setup](#ollama-model-setup)
5. [Starting the App](#starting-the-app)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

---

## Prerequisites

Before you begin, ensure the following are installed on your Windows machine:

| Requirement | Minimum Version | Download / Check |
|---|---|---|
| **Windows** | 10 (build 19041+) or 11 | `winver` |
| **PowerShell** | 5.1 (7.x recommended) | `$PSVersionTable.PSVersion` |
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com/download/win) |
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Ollama** | Latest | [ollama.com/download](https://ollama.com/download) |

**Optional but recommended:**

- **Node.js** 20+ — required if you also want to run the legacy `lantern-garage` Node surface.
- **CUDA** — only if you intend to run PyTorch on GPU instead of CPU.

> **Note:** The installer script will check all prerequisites and warn you if anything is missing.

---

## Quick Start (One-Click Installer)

The fastest way to get Dream Journal running.

### 1. Open PowerShell as Administrator

Right-click the Start menu and select **Terminal (Admin)** or **PowerShell (Admin)**.

### 2. Run the installer

```powershell
irm https://raw.githubusercontent.com/alex-place/lantern-os/master/scripts/install-dream-journal.ps1 | iex
```

**What the script does:**

1. Validates prerequisites (Git, Python, Ollama).
2. Clones `https://github.com/alex-place/lantern-os.git` to `~\lantern-os` (or updates an existing clone).
3. Creates a Python virtual environment at `~\lantern-os\.venv`.
4. Installs all Python dependencies from `requirements.txt`.
5. Installs the CPU-optimized PyTorch stack (`torch`, `torchvision`, `torchaudio`).
6. Installs AI/ML libraries (`sentence-transformers`, `faiss-cpu`).
7. Pulls the required Ollama models (`llama3.2:3b`, `nomic-embed-text`).
8. Installs Node.js dependencies for the `lantern-garage` surface (if Node is present).
9. Creates a desktop shortcut named **Dream Journal**.
10. Optionally launches the server and opens your browser.

**Estimated time:** 5–10 minutes depending on download speed.

> **Safe to re-run:** The installer is idempotent. Running it again will update the repo and dependencies without wiping your data.

---

## Manual Install

If the one-click installer fails or you prefer full control, follow these steps.

### Step 1 — Clone the repository

```powershell
cd $env:USERPROFILE
git clone https://github.com/alex-place/lantern-os.git
cd lantern-os
```

### Step 2 — Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> **Why a venv?** Keeps Lantern OS dependencies isolated from your global Python installation.

### Step 3 — Install Python dependencies

```powershell
pip install -r requirements.txt
pip install sentence-transformers faiss-cpu torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

If you have an NVIDIA GPU and want CUDA support, omit the `--index-url` argument:

```powershell
pip install sentence-transformers faiss-cpu torch torchvision torchaudio
```

### Step 4 — Install Node.js dependencies (optional)

Only needed if you plan to run the legacy `lantern-garage` Node surface:

```powershell
cd apps\lantern-garage
npm install
cd ..\..
```

### Step 5 — Pull Ollama models

Ensure Ollama is running in the background (check the system tray), then:

```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

---

## Ollama Model Setup

Dream Journal uses two local models via Ollama:

| Model | Purpose | Size | Pull Command |
|---|---|---|---|
| `llama3.2:3b` | Chat / inference | ~2.0 GB | `ollama pull llama3.2:3b` |
| `nomic-embed-text` | Text embeddings / RAG | ~274 MB | `ollama pull nomic-embed-text` |

**Verify both models are present:**

```powershell
ollama list
```

You should see:

```
NAME                    ID              SIZE      MODIFIED
llama3.2:3b             ...             2.0 GB    ...
nomic-embed-text:latest ...             274 MB    ...
```

---

## Starting the App

### Python / Dream Journal (primary)

With your virtual environment activated:

```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn apps.lantern-garage.server:app --host 127.0.0.1 --port 4177 --reload
```

Then open: [http://127.0.0.1:4177](http://127.0.0.1:4177)

### Legacy Node.js surface (optional)

If you want the original `lantern-garage` Node dashboard:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternGarageApp.ps1
```

---

## Verification

After starting the server, verify everything is healthy:

```powershell
# API health check
Invoke-RestMethod -Uri "http://127.0.0.1:4177/api/health"

# Expected output:
# {
#   "ok": true,
#   "service": "lantern-garage",
#   "generatedAt": "..."
# }
```

**In your browser:**

- Open [http://127.0.0.1:4177](http://127.0.0.1:4177)
- You should see the Dream Journal / Lantern Garage interface.
- Try the AI chat or RAG search features to confirm models are responding.

---

## Troubleshooting

### `irm` is blocked or execution policy is restricted

Run PowerShell as **Administrator**, then:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then re-run the installer.

### `python` or `pip` not found

Ensure Python was installed with **"Add Python to PATH"** checked. If missed, reinstall or manually add Python to your system `PATH`.

### Ollama models fail to pull

1. Confirm Ollama is running (check the system tray icon).
2. If behind a corporate proxy, configure proxy settings in Ollama.
3. Try pulling manually: `ollama pull llama3.2:3b`

### `uvicorn` fails to start with "Module not found"

Ensure your virtual environment is activated (you should see `(.venv)` in your prompt):

```powershell
.venv\Scripts\Activate.ps1
```

### Port 4177 is already in use

Either close the existing process or start on a different port:

```powershell
python -m uvicorn apps.lantern-garage.server:app --host 127.0.0.1 --port 5177 --reload
```

### PyTorch / FAISS installation errors on Windows

If you see compiler errors, ensure you are using the CPU wheel index:

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

For FAISS on Windows, use the pre-built binary:

```powershell
pip install faiss-cpu
```

### Desktop shortcut not created

The shortcut is created only for the current user profile. If you need it elsewhere, copy the `.lnk` file from your Desktop or create a new one pointing to:

```
Target: powershell.exe
Arguments: -NoProfile -ExecutionPolicy Bypass -File "%USERPROFILE%\lantern-os\scripts\Start-DreamJournal.ps1"
```

---

## Next Steps

Now that Dream Journal is installed:

1. **Run the convergence loop** to validate your environment:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
   ```

2. **Open the operator cockpit** (Tony Garage):
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Open-TonyGarage.ps1
   ```

3. **Read the architecture docs** in `docs/NOVEL-KUBERNETES-RAG-INTEGRATION.md` to understand the RAG pipeline.

4. **Check v1.0 readiness:**
   ```powershell
   Get-Content reports\V1-READINESS-TEST-2026-05-26.md
   ```

---

## File Reference

| File | Purpose |
|---|---|
| `scripts/install-dream-journal.ps1` | One-click installer (this guide) |
| `scripts/Start-LanternGarageApp.ps1` | Legacy Node.js launcher |
| `scripts/Invoke-LanternConvergenceLoop.ps1` | Convergence / health loop |
| `scripts/Open-TonyGarage.ps1` | Operator cockpit |
| `apps/lantern-garage/` | Primary application surface |
| `docs/` | Architecture, runbooks, and deep-dives |
| `manifests/` | Release lanes and validation |

---

**Happy journaling. Light the lantern.**
