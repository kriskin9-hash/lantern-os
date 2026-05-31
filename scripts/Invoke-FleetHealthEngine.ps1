param(
    [string]$OutputPath = "D:\tmp\lantern-os\data\automation\fleet-health-results.json",
    [switch]$RunOnce
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Get-SystemHealth {
    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'" -ErrorAction SilentlyContinue
    $osDisk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction SilentlyContinue
    
    return @{
        dDrive = @{
            exists = $disk -ne $null
            freeGB = if ($disk) { [Math]::Round($disk.FreeSpace / 1GB, 2) } else { 0 }
            totalGB = if ($disk) { [Math]::Round($disk.Size / 1GB, 2) } else { 0 }
            percentFree = if ($disk -and $disk.Size -gt 0) { [Math]::Round($disk.FreeSpace / $disk.Size * 100, 1) } else { 0 }
        }
        cDrive = @{
            freeGB = if ($osDisk) { [Math]::Round($osDisk.FreeSpace / 1GB, 2) } else { 0 }
            totalGB = if ($osDisk) { [Math]::Round($osDisk.Size / 1GB, 2) } else { 0 }
            percentFree = if ($osDisk -and $osDisk.Size -gt 0) { [Math]::Round($osDisk.FreeSpace / $osDisk.Size * 100, 1) } else { 0 }
        }
        memory = @{
            totalGB = [Math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
        }
    }
}

function Test-SafetyGates {
    $windsurfHooks = Test-Path "D:\tmp\lantern-os\.windsurf\hooks.json"
    $convergenceLoop = Test-Path "D:\tmp\lantern-os\scripts\Invoke-LanternConvergenceLoop.ps1"
    $agentsMd = Test-Path "D:\tmp\lantern-os\AGENTS.md"
    
    return @{
        windsurfHooks = $windsurfHooks
        convergenceLoop = $convergenceLoop
        agentsMd = $agentsMd
        allGates = $windsurfHooks -and $convergenceLoop -and $agentsMd
    }
}

function Invoke-FleetHealthEngine {
    Write-Log "=== Fleet Health Engine Started ==="
    
    $health = Get-SystemHealth
    $gates = Test-SafetyGates
    
    $alerts = @()
    if ($health.dDrive.percentFree -lt 20) { $alerts += "D: drive low space" }
    if ($health.cDrive.percentFree -lt 10) { $alerts += "C: drive critical" }
    if (-not $gates.allGates) { $alerts += "Safety gates incomplete" }
    
    $results = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Fleet Health Engine v1.0"
        system = $health
        safetyGates = $gates
        alerts = $alerts
        healthy = $alerts.Count -eq 0
        nextAction = if ($alerts.Count -gt 0) { "Address alerts: $($alerts -join '; ')" } else { "System healthy" }
    }
    
    $results | ConvertTo-Json -Depth 5 | Set-Content $OutputPath
    Write-Log "Health check complete, $($alerts.Count) alerts"
    
    return $results
}

if ($RunOnce -or -not $RunOnce) {
    Invoke-FleetHealthEngine
}
