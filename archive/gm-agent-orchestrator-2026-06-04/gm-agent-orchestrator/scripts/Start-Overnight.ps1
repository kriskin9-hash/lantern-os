[CmdletBinding()]
param(
    [string]$ProjectName = "",
    [switch]$Status,
    [switch]$Stop,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$startScript = Join-Path $PSScriptRoot "Start-GmAgentOrchestrator.ps1"
$agents = Get-Content (Join-Path $root "config\agents.json") -Raw | ConvertFrom-Json

function Get-SlotProcess {
    param([string]$SlotName)

    $needle = 'agent-worktrees\\' + [Regex]::Escape($SlotName) + '(\b|"|\\)'

    return Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match 'Start-AgentSlot' -and
            $_.CommandLine -match $needle
        }
}

if ($Status) {
    foreach ($slot in $agents.slots) {
        $procs = @(Get-SlotProcess -SlotName $slot.name)
        $statePath = Join-Path $root ("status\{0}.json" -f $slot.name)
        $state = "(no status)"
        if (Test-Path $statePath) {
            try { $state = (Get-Content $statePath -Raw | ConvertFrom-Json).state } catch {}
        }
        $enabled = if ($slot.enabled) { "enabled" } else { "disabled" }
        $running = if ($procs.Count -gt 0) { "PID=" + (($procs.ProcessId) -join ",") } else { "not running" }
        "{0,-14} {1,-9} {2,-12} state={3}" -f $slot.name, $enabled, $running, $state | Write-Host
    }
    return
}

if ($Stop) {
    foreach ($slot in $agents.slots) {
        foreach ($p in (Get-SlotProcess -SlotName $slot.name)) {
            if ($DryRun) {
                Write-Host "[dry-run] Would stop $($slot.name) PID $($p.ProcessId)"
            }
            else {
                Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "Stopped slot $($slot.name) PID $($p.ProcessId)"
            }
        }
    }
    return
}

foreach ($slot in $agents.slots) {
    if (-not $slot.enabled) {
        Write-Host "Skipping disabled slot: $($slot.name)"
        continue
    }

    $existing = @(Get-SlotProcess -SlotName $slot.name)
    if ($existing.Count -gt 0) {
        Write-Host "Slot $($slot.name) already running as PID $(($existing.ProcessId) -join ',')"
        continue
    }

    if ($DryRun) {
        Write-Host "[dry-run] Would launch slot: $($slot.name)"
        continue
    }

    Write-Host "Launching slot: $($slot.name)"
    $launchArgs = @("-SlotName", $slot.name)
    if (-not [string]::IsNullOrWhiteSpace($ProjectName)) {
        $launchArgs += @("-ProjectName", $ProjectName)
    }
    & $startScript @launchArgs
    Start-Sleep -Milliseconds 1500
    $now = @(Get-SlotProcess -SlotName $slot.name)
    if ($now.Count -gt 0) {
        Write-Host "  -> running PID=$(($now.ProcessId) -join ',')"
    }
    else {
        Write-Warning "  -> slot did not appear to start. Check $root\logs\$($slot.name)\."
    }
}

Write-Host ""
Write-Host "Overnight mode online. Slots loop until queue is empty (then sleep 60s and retry)."
Write-Host "Status:  scripts\Start-Overnight.ps1 -Status"
Write-Host "Stop:    scripts\Start-Overnight.ps1 -Stop"
Write-Host "Dashboard: http://localhost:8765/dashboard/"
