[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$scriptUnderTest = Join-Path $Root "scripts\Start-ActiveAgentFleet.ps1"
if (-not (Test-Path -LiteralPath $scriptUnderTest -PathType Leaf)) {
    throw "Required script not found: $scriptUnderTest"
}

function New-TestRoot {
    $path = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-active-fleet-{0}" -f [Guid]::NewGuid().ToString("N"))
    foreach ($relative in @("config", "scripts", "status")) {
        New-Item -ItemType Directory -Force -Path (Join-Path $path $relative) | Out-Null
    }
    return $path
}

function Write-BaseConfig {
    param([string]$Path)

    @'
{
  "activeProcessing": {
    "enabled": true,
    "immediateDispatch": true,
    "noQueueDelay": true
  },
  "agentActivation": {
    "standbyActivation": true,
    "maxActiveAgents": 2
  },
  "mcpIntegration": {
    "serverUrl": "http://127.0.0.1:8787"
  }
}
'@ | Set-Content -LiteralPath (Join-Path $Path "config\active-processing.json") -Encoding UTF8

    @'
{
  "routingPolicy": {
    "dispatchOrder": [
      { "slot": "gemini-flash" },
      { "slot": "codex-main" },
      { "slot": "claude-main" }
    ]
  }
}
'@ | Set-Content -LiteralPath (Join-Path $Path "config\agents.json") -Encoding UTF8
}

function Write-StatusStub {
    param(
        [string]$Path,
        [string]$Json
    )

    @"
[CmdletBinding()]
param([string]`$Root = "")
Write-Output @'
$Json
'@
"@ | Set-Content -LiteralPath (Join-Path $Path "scripts\Get-OrchestratorStatus.ps1") -Encoding UTF8
}

function Initialize-GitRepo {
    param([string]$Path)

    & git -C $Path init | Out-Null
    & git -C $Path config user.email "agent@test.local" | Out-Null
    & git -C $Path config user.name "agent:test" | Out-Null
    & git -C $Path add . | Out-Null
    & git -C $Path commit -m "init" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create baseline git repo at $Path"
    }
}

function Invoke-Plan {
    param([string]$Path)

    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptUnderTest -Root $Path 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Start-ActiveAgentFleet.ps1 failed with exit code $LASTEXITCODE. Output: $($output -join "`n")"
    }
    return (($output | ForEach-Object { $_.ToString() }) -join "`n") | ConvertFrom-Json -ErrorAction Stop
}

$blockedRoot = New-TestRoot
$readyRoot = New-TestRoot

try {
    Write-BaseConfig -Path $blockedRoot
    Write-StatusStub -Path $blockedRoot -Json @'
{
  "state": "needs_attention",
  "headline": "Inspect failed task converge-founder-needs-ordered-worklist.md before claiming new queue work.",
  "queueRecommendation": {
    "recommendedAction": "inspect",
    "from": "failed",
    "taskName": "converge-founder-needs-ordered-worklist.md",
    "reason": "Failed task exists and no active work is present; inspect failure evidence before retrying to avoid repeated token burn."
  },
  "nextAction": {
    "action": "Inspect failed task first.",
    "owner": "Alex",
    "when": "now",
    "blockedBy": "converge-founder-needs-ordered-worklist.md"
  },
  "availability": {
    "availableCount": 1,
    "slots": [
      {
        "slot": "gemini-flash",
        "agent": "gemini",
        "state": "idle",
        "wakeState": "available",
        "safeToWake": true,
        "reason": "ready",
        "nextAction": "Start an available slot on queued work."
      }
    ]
  },
  "serviceHealth": {
    "mcpCapability": {
      "mode": "online_writable",
      "writable": true
    }
  }
}
'@
    Initialize-GitRepo -Path $blockedRoot
    "dirty" | Set-Content -LiteralPath (Join-Path $blockedRoot "scripts\Start-OrchMcpServer.Tools.ps1") -Encoding UTF8

    $blockedPlan = Invoke-Plan -Path $blockedRoot
    if ($blockedPlan.parallelPlan.dispatchMode -ne "hold_for_mcp_p0") {
        throw "Expected hold_for_mcp_p0 dispatch mode; got $($blockedPlan.parallelPlan.dispatchMode)."
    }
    if (-not $blockedPlan.mcpLane.blocked) {
        throw "Expected MCP lane to be blocked when local control-plane files are dirty."
    }
    if (@($blockedPlan.parallelPlan.selectedSlots).Count -ne 0) {
        throw "Blocked plan must not select slots for parallel activation."
    }
    if (@($blockedPlan.parallelPlan.futureSlotsAfterMcpFix).Count -ne 1) {
        throw "Blocked plan should preserve the future candidate slot set."
    }
    if (@($blockedPlan.repo.controlPlaneDirtyFiles).Count -ne 1) {
        throw "Expected exactly one MCP/control-plane dirty file in blocked scenario."
    }
    if (@($blockedPlan.mcpLane.blockedReasons) -notcontains "inspect_required_before_retry") {
        throw "Expected blocked reasons to include inspect_required_before_retry."
    }

    Write-BaseConfig -Path $readyRoot
    Write-StatusStub -Path $readyRoot -Json @'
{
  "state": "queued",
  "headline": "Queued work is ready.",
  "queueRecommendation": {
    "recommendedAction": "claim",
    "from": "queue",
    "taskName": "restore-orchestrator-agent-fleet-health.md",
    "reason": "Safe queued work is available."
  },
  "nextAction": {
    "action": "Start an available slot on queued work.",
    "owner": "Alex",
    "when": "now",
    "blockedBy": "none"
  },
  "availability": {
    "availableCount": 3,
    "slots": [
      {
        "slot": "codex-main",
        "agent": "codex",
        "state": "idle",
        "wakeState": "available",
        "safeToWake": true,
        "reason": "ready",
        "nextAction": "Start an available slot on queued work."
      },
      {
        "slot": "claude-main",
        "agent": "claude",
        "state": "idle",
        "wakeState": "available",
        "safeToWake": true,
        "reason": "ready",
        "nextAction": "Start an available slot on queued work."
      },
      {
        "slot": "gemini-flash",
        "agent": "gemini",
        "state": "idle",
        "wakeState": "available",
        "safeToWake": true,
        "reason": "ready",
        "nextAction": "Start an available slot on queued work."
      }
    ]
  },
  "serviceHealth": {
    "mcpCapability": {
      "mode": "online_writable",
      "writable": true
    }
  }
}
'@
    Initialize-GitRepo -Path $readyRoot

    $readyPlan = Invoke-Plan -Path $readyRoot
    if ($readyPlan.parallelPlan.dispatchMode -ne "parallel_ready") {
        throw "Expected parallel_ready dispatch mode; got $($readyPlan.parallelPlan.dispatchMode)."
    }
    if ($readyPlan.mcpLane.blocked) {
        throw "Expected MCP lane to be unblocked in clean ready scenario."
    }
    if (@($readyPlan.parallelPlan.selectedSlots).Count -ne 2) {
        throw "Expected selected slots to honor maxActiveAgents=2."
    }
    $selectedNames = @($readyPlan.parallelPlan.selectedSlots | ForEach-Object { $_.slot })
    if (($selectedNames -join ",") -ne "gemini-flash,codex-main") {
        throw "Expected dispatch order gemini-flash,codex-main; got $($selectedNames -join ',')."
    }

    Write-Host "Active agent fleet plan test passed."
}
finally {
    Remove-Item -LiteralPath $blockedRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $readyRoot -Recurse -Force -ErrorAction SilentlyContinue
}
