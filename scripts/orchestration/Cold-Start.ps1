#!/usr/bin/env pwsh
# Cold-Start.ps1
# Run from repo root: powershell -ExecutionPolicy Bypass -File .\Cold-Start.ps1
# Follows the contract in PR #218 comment (Alex cold-start guide)

$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

$pass = 0; $fail = 0; $warn = 0
$root = $PSScriptRoot
$ngrokGatewayPort = 8787
$ngrokHost = "crinkle-utmost-debit.ngrok-free.app"

function ok($msg)   { Write-Host "  [PASS] $msg" -ForegroundColor Green;  $script:pass++ }
function err($msg)  { Write-Host "  [FAIL] $msg" -ForegroundColor Red;    $script:fail++ }
function warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow; $script:warn++ }
function hdr($msg)  { Write-Host ""; Write-Host "=== $msg ===" -ForegroundColor Cyan }

# -- 1. Sync ------------------------------------------------------------------
hdr "1. Sync"
& git fetch origin 2>&1 | Out-Null
& git checkout master 2>&1 | Out-Null
& git pull --ff-only origin master 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { ok "git pull --ff-only succeeded" }
else { warn "pull had warnings (may be up to date)" }

# -- 2. Repo health -----------------------------------------------------------
hdr "2. Repo health"

$gitStatus = & git status --short | Where-Object { $_ -notmatch '^\?\? Cold-Start' }
if (-not $gitStatus) { ok "git status clean" }
else {
    warn "Untracked/modified files:"
    $gitStatus | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-PowerShellSyntax.ps1 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { ok "Test-PowerShellSyntax" } else { err "Test-PowerShellSyntax FAILED" }

& powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-OrchestratorStatusJson.ps1 -Root $root 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { ok "Test-OrchestratorStatusJson" } else { err "Test-OrchestratorStatusJson FAILED" }

# -- 3. Queue / status snapshot (read-only) -----------------------------------
hdr "3. Queue / status snapshot"

$status = & powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Get-OrchestratorStatus.ps1 -Root $root 2>&1 |
    Where-Object { $_ -notmatch '^WARNING' } | ConvertFrom-Json -ErrorAction SilentlyContinue

if ($status) {
    ok "Status JSON parsed"
    Write-Host "  State    : $($status.state)"
    Write-Host "  Queue    : $($status.counts.queue)"
    Write-Host "  Active   : $($status.counts.active)"
    Write-Host "  Done     : $($status.counts.done)"
    Write-Host "  Failed   : $($status.counts.failed)"
    if ($status.counts.active -gt 0) { warn "Active work in progress - do not start more agents" }
    if ($status.counts.failed -gt 0) { warn "$($status.counts.failed) failed task(s) - inspect before requeuing" }
} else {
    err "Could not parse status JSON"
}

Write-Host ""
Write-Host "  Queue tasks:" -ForegroundColor Gray
Get-ChildItem .\tasks\queue -File -Filter *.md -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host "    $($_.Name)" -ForegroundColor Gray }

Write-Host "  Active tasks:" -ForegroundColor Gray
$activeTasks = Get-ChildItem .\tasks\active -File -Filter *.md -ErrorAction SilentlyContinue
if ($activeTasks) { $activeTasks | ForEach-Object { Write-Host "    $($_.Name)" -ForegroundColor Yellow } }
else { Write-Host "    (none)" -ForegroundColor Gray }

Write-Host "  Failed tasks:" -ForegroundColor Gray
Get-ChildItem .\tasks\failed -File -Filter *.md -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host "    $($_.Name)" -ForegroundColor Gray }

# -- 4. MCP / server / ngrok health ------------------------------------------
hdr "4. MCP / server / ngrok health"

$mcpUp = $false
try {
    Invoke-RestMethod http://127.0.0.1:8788/health -TimeoutSec 3 | Out-Null
    ok "MCP server responding on :8788"
    $mcpUp = $true
} catch {
    warn "MCP server not responding on :8788"
    Write-Host "    Start : powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-OrchMcpServer.ps1" -ForegroundColor Gray
}

try {
    Invoke-RestMethod "http://127.0.0.1:$ngrokGatewayPort/health" -TimeoutSec 3 | Out-Null
    ok "Local ngrok/gateway target responding on :$ngrokGatewayPort"
} catch {
    Write-Host "  [:$ngrokGatewayPort] not responding locally (may be expected if gateway is external-only or down)" -ForegroundColor Gray
}

$ngrok = Get-Process ngrok -ErrorAction SilentlyContinue
if ($ngrok) {
    ok "ngrok running (pid $($ngrok.Id))"
} else {
    warn "ngrok not running - MCP not reachable from GPT Web or Claude"
    Write-Host "    Start in a separate prompt: ngrok http $ngrokGatewayPort --url $ngrokHost" -ForegroundColor Gray
}

try {
    Invoke-RestMethod "https://$ngrokHost/health" -TimeoutSec 5 | Out-Null
    ok "ngrok tunnel reachable externally"
} catch {
    Write-Host "  [INFO] ngrok tunnel not reachable externally (expected if ngrok is down or URL changed)" -ForegroundColor Gray
}

# -- 5. Post-merge validation suite ------------------------------------------
hdr "5. Post-merge validation suite"

# Tests requiring -Root (PSScriptRoot is empty under powershell -File invocation)
foreach ($t in @("tests\Test-TaskMovement.ps1", "tests\Test-QueueClaimHardness.ps1")) {
    if (-not (Test-Path $t)) { warn "Not found (skip): $t"; continue }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $t -Root $root 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { ok $t } else { err "$t FAILED" }
}

# Stale branch test: git emits informational stderr ("Switched to new branch")
# which causes a false failure in the outer shell - filter it out
$staleTest = "tests\Test-StaleBranchStatusContract.ps1"
if (Test-Path $staleTest) {
    $staleOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $staleTest -Root $root 2>&1
    $meaningful = $staleOut | Where-Object { $_ -notmatch "Switched to" -and $_ -notmatch "NativeCommandError" -and $_ -notmatch "CategoryInfo" -and $_ -notmatch "FullyQualified" }
    $lastLine = ($meaningful | Select-Object -Last 1)
    if ($lastLine -match 'passed|Validated') { ok "$staleTest" }
    else { err "$staleTest FAILED: $lastLine" }
} else { warn "Not found (skip): $staleTest" }

# Safe PowerShell runner test
$safeTest = "tests\Test-SafePowerShellRunner.ps1"
if (Test-Path $safeTest) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $safeTest 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { ok $safeTest } else { err "$safeTest FAILED" }
} else { warn "Not found (skip): $safeTest" }

# -- 6. Slot readiness --------------------------------------------------------
hdr "6. Slot readiness"

if ($status) {
    foreach ($slot in $status.slots) {
        $color = switch ($slot.state) {
            "idle"     { "Green" }
            "disabled" { "Gray" }
            default    { "Yellow" }
        }
        Write-Host ("  {0,-14} agent={1,-10} state={2}" -f $slot.name, $slot.agent, $slot.state) -ForegroundColor $color
    }
}

# -- 7. Go / No-go ------------------------------------------------------------
hdr "7. Go / No-go"

Write-Host ""
Write-Host ("  PASS={0}  FAIL={1}  WARN={2}" -f $pass, $fail, $warn) -ForegroundColor White

if ($fail -gt 0) {
    Write-Host ""
    Write-Host "  NO-GO: $fail failure(s). Fix before starting agents." -ForegroundColor Red
    Write-Host "  Per contract: do not start agents, do not bulk requeue." -ForegroundColor Red
} elseif (-not $mcpUp) {
    Write-Host ""
    Write-Host "  NO-GO: MCP server is down. Start it first:" -ForegroundColor Yellow
    Write-Host "    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-OrchMcpServer.ps1" -ForegroundColor Yellow
    Write-Host "    Then start ngrok in a separate prompt: ngrok http $ngrokGatewayPort --url $ngrokHost" -ForegroundColor Yellow
} elseif (-not $ngrok) {
    Write-Host ""
    Write-Host "  CAUTION: MCP is local-only (ngrok down). GPT Web and Claude cannot reach it." -ForegroundColor Yellow
    Write-Host "  Start ngrok in a separate prompt: ngrok http $ngrokGatewayPort --url $ngrokHost" -ForegroundColor Yellow
    Write-Host "  GO for local agent start only." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "  GO: all checks pass. Safe to start a slot." -ForegroundColor Green
    if ($status) {
        Write-Host "  Suggested next slot : $($status.availability.nextWakeSlot)" -ForegroundColor Green
        Write-Host "  Tasks in queue      : $($status.counts.queue)" -ForegroundColor Green
    }
}

Write-Host ""

