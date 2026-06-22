# Continual training loop for the Sigma0 Ouro coder (tool-call / agentic traces).
#
# Each run RE-EXTRACTS tool-call traces from ALL current Claude Code sessions
# (the extractor scans ~/.claude/projects/*, so new sessions are picked up
# automatically) and trains a fresh LoRA adapter on the grown dataset. This is
# how the corpus grows toward 20k over time: keep using Claude Code, re-run this.
#
# Adapted for THIS machine (krisk / RTX 4070 SUPER, C: only -- no D: drive).
# The upstream scripts/continual-train.ps1 targets the Qwen+Ollama+D: path.
#
# Run manually:  powershell -ExecutionPolicy Bypass -File scripts/continual-train-ouro.ps1
# Schedule weekly (operator opt-in):
#   schtasks /Create /TN "Sigma0OuroContinualTrain" /TR "powershell -ExecutionPolicy Bypass -File C:\Users\krisk\Desktop\lanternOS\scripts\continual-train-ouro.ps1" /SC WEEKLY /D SUN /ST 03:00 /F

param(
  [int]$Epochs = 1,
  [int]$Seq = 768,
  [int]$Batch = 4,
  [int]$GradAccum = 4,
  [string]$Base = "ByteDance/Ouro-1.4B",
  [switch]$SkipDataRefresh
)

$ErrorActionPreference = "Stop"
$repo = "C:\Users\krisk\Desktop\lanternOS"
$py   = "$repo\.venv-train\Scripts\python.exe"
$data = "$repo\models\lantern-sigma0-coder\tool-call-traces.jsonl"
Set-Location $repo
$env:HF_HOME = "C:\hf-cache"

function Log($m) { $ts = (Get-Date).ToString("s"); Write-Output "[$ts] $m"; Add-Content "$repo\data\continual-training-ouro.log" "[$ts] $m" }

# Version = next free C:\lantern-train\ouro-sigma0-v* dir
$existing = Get-ChildItem "C:\lantern-train" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^ouro-sigma0-v(\d+)' } | ForEach-Object { [int]($_.Name -replace '\D','') }
$next = 1; if ($existing) { $next = ($existing | Measure-Object -Maximum).Maximum + 1 }
$out = "C:\lantern-train\ouro-sigma0-v$next-toolcalls"
Log "continual run -> adapter v$next ($out)"

if (-not $SkipDataRefresh) {
  Log "refreshing tool-call traces from all Claude sessions..."
  & $py "$repo\scripts\extract-tool-call-traces.py" --out $data
  if ($LASTEXITCODE -ne 0) { Log "extract FAILED"; exit 1 }
}
$rows = (Get-Content $data | Measure-Object -Line).Lines
Log "dataset rows: $rows"

Log "training (epochs=$Epochs seq=$Seq batch=$Batch accum=$GradAccum)..."
& $py "$repo\scripts\train-qlora-ouro.py" --base $Base --data $data --out $out --epochs $Epochs --seq $Seq --batch $Batch --grad-accum $GradAccum
if ($LASTEXITCODE -ne 0) { Log "train FAILED"; exit 1 }

Log "done. adapter -> $out\final"
Log "serve it:  `$env:OURO_MODEL='$Base'; `$env:OURO_ADAPTER='$out\final'; $py $repo\scripts\ouro_serve.py"
