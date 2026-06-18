# Continual training loop for the local Σ₀ coding agent.
#
# Each run: refresh training data from the latest Claude sessions + successful
# autowork outcomes, train a NEW LoRA version, merge, deploy to Ollama, and
# point OLLAMA_MODEL at it. The performance leaderboard (agent-performance.jsonl)
# then arbitrates which version actually gets work — so quality only ratchets up.
#
# Run manually:   powershell -ExecutionPolicy Bypass -File scripts/continual-train.ps1
# Scheduled:      see scripts/continual-train.ps1 -Register (or the cron/task wiring)
#
# Env: HF_HOME + OLLAMA_MODELS already persisted to D:. GPU = RTX 3070 (8 GB) -> 3B base.

param(
  [int]$Epochs = 3,
  [string]$Base = "Qwen/Qwen2.5-Coder-3B-Instruct",
  [switch]$SkipDataRefresh
)

$ErrorActionPreference = "Stop"
$repo = "C:\dev\lantern-os"
$py   = "$repo\.venv-train\Scripts\python.exe"
$work = "D:\lantern-train"
$ollama = "C:\Users\alexp\AppData\Local\Programs\Ollama\ollama.exe"
Set-Location $repo
$env:HF_HOME = "D:\hf-cache"
$env:OLLAMA_MODELS = "D:\ollama-models"

function Log($m) { $ts = (Get-Date).ToString("s"); Write-Output "[$ts] $m"; Add-Content "$repo\data\continual-training.log" "[$ts] $m" }

# 1. Next version number (probe existing ollama models)
$existing = & $ollama list 2>$null | Select-String "lantern-sigma0-coder-v(\d+)" -AllMatches |
  ForEach-Object { $_.Matches } | ForEach-Object { [int]$_.Groups[1].Value }
$next = (($existing | Measure-Object -Maximum).Maximum + 1)
if (-not $next -or $next -lt 2) { $next = 3 }
$model = "lantern-sigma0-coder-v$next"
Log "Continual train -> $model (base $Base, $Epochs epochs)"

# 2. Refresh training data from latest sessions
if (-not $SkipDataRefresh) {
  Log "Extracting fresh Claude-session pairs..."
  & $py scripts/extract-session-pairs.py | Out-Null
  & $py scripts/convert-pairs-to-alpaca.py | Out-Null
  Log "Training data refreshed."
}

# 3. Train new LoRA version
$adapters = "$work\sigma0-adapters-v$next"
Log "Training QLoRA..."
& $py scripts/train-qlora-peft.py --base $Base --data "models/lantern-sigma0-coder/training-data.jsonl" --out $adapters --epochs $Epochs
if ($LASTEXITCODE -ne 0) { Log "TRAIN FAILED (exit $LASTEXITCODE) — aborting, keeping current model."; exit 1 }

# 4. Merge adapter -> fp16
$merged = "$work\sigma0-merged-v$next"
Log "Merging adapter..."
& $py scripts/merge-lora.py $Base "$adapters\final" $merged
if ($LASTEXITCODE -ne 0) { Log "MERGE FAILED — aborting."; exit 1 }

# 5. Deploy to Ollama
$mf = "$work\Modelfile.v$next"
@"
FROM $merged
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
SYSTEM """You are the Lantern Σ₀ coding agent, continually fine-tuned on this project's own engineering sessions. Edit via exact SEARCH/REPLACE blocks; change only what the task needs; fix root causes; cite evidence. No emojis unless asked; no trailing summaries."""
"@ | Set-Content -Encoding utf8 $mf
Log "Deploying $model to Ollama..."
& $ollama create $model -f $mf
if ($LASTEXITCODE -ne 0) { Log "OLLAMA CREATE FAILED — aborting."; exit 1 }

# 6. Promote: point OLLAMA_MODEL at the new version. The leaderboard then decides
#    real work allocation; rollback = set OLLAMA_MODEL back to a prior vN.
$envFile = "$repo\.env.local"
if (Test-Path $envFile) {
  (Get-Content $envFile) -replace '^OLLAMA_MODEL=.*', "OLLAMA_MODEL=$model" | Set-Content -Encoding utf8 $envFile
  if (-not (Select-String -Path $envFile -Pattern '^OLLAMA_MODEL=' -Quiet)) { Add-Content $envFile "OLLAMA_MODEL=$model" }
}
[Environment]::SetEnvironmentVariable("OLLAMA_MODEL", $model, "User")
Log "Promoted $model (OLLAMA_MODEL updated). Leaderboard will arbitrate real usage."
Log "DONE. Restart dev servers to pick up the new model."
