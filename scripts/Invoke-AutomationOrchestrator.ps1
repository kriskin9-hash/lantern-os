param(
    [string]$ConfigPath = "D:\tmp\lantern-os\data\automation\orchestrator-config.json",
    [switch]$RunOnce,
    [switch]$DryRun,
    [int]$MainLoopIntervalMinutes = 10
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    
    # Also write to log file
    $logPath = "D:\tmp\lantern-os\data\automation\orchestrator.log"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logPath -Value $logMessage
}

function Get-OrchestratorConfig {
    param([string]$ConfigFile)
    
    if (Test-Path $ConfigFile) {
        try {
            $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
            return $config
        }
        catch {
            Write-Log "Failed to load config: $_" "ERROR"
            return $null
        }
    }
    
    # Return default configuration
    return @{
        components = @(
            @{
                name = "git-auto-deploy"
                script = "D:\tmp\lantern-os\scripts\Invoke-GitAutoDeploy.ps1"
                enabled = $true
                priority = 1
                intervalMinutes = 5
            }
            @{
                name = "auto-poll"
                script = "D:\tmp\lantern-os\scripts\Invoke-AutoPoll.ps1"
                enabled = $true
                priority = 2
                intervalMinutes = 5
            }
            @{
                name = "hff-convergence"
                script = "D:\tmp\lantern-os\scripts\Invoke-HFFConvergence.ps1"
                enabled = $true
                priority = 3
                intervalMinutes = 10
            }
            @{
                name = "lantern-convergence"
                script = "D:\tmp\lantern-os\scripts\Invoke-LanternConvergenceLoop.ps1"
                enabled = $true
                priority = 4
                intervalMinutes = 15
            }
        )
        mainLoop = @{
            enabled = $true
            intervalMinutes = 10
            healthCheckInterval = 30
        }
    }
}

function Invoke-Component {
    param(
        [object]$Component,
        [bool]$DryRun
    )
    
    $name = $Component.name
    $script = $Component.script
    $enabled = $Component.enabled
    
    Write-Log "Component details: name=$name, enabled=$enabled, script=$script"
    
    if (-not $enabled) {
        Write-Log "Component disabled: $name"
        return $false
    }
    
    if (-not (Test-Path $script)) {
        Write-Log "Script not found: $script" "WARN"
        return $false
    }
    
    Write-Log "Executing component: $name"
    
    try {
        if ($DryRun) {
            Write-Log "[DRY RUN] Would execute: $script"
            return $true
        }
        
        & $script -RunOnce
        $success = $LASTEXITCODE -eq 0
        
        if ($success) {
            Write-Log "Component succeeded: $name"
        } else {
            Write-Log "Component failed with exit code ${LASTEXITCODE}: $name" "ERROR"
        }
        
        return $success
    }
    catch {
        Write-Log "Component error: $_" "ERROR"
        return $false
    }
}

function Run-HealthCheck {
    param([string]$RepoPath = "D:\tmp\lantern-os")
    
    Write-Log "Running health check"
    
    Push-Location $RepoPath
    try {
        # Check git status
        $status = git status --porcelain
        $isDirty = $status.Length -gt 0
        
        # Check network connectivity
        $networkOk = Test-Connection github.com -Count 1 -Quiet
        
        # Check disk space
        $drive = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
        $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
        
        $health = @{
            gitDirty = $isDirty
            networkOk = $networkOk
            diskSpaceGB = $freeSpaceGB
            timestamp = Get-Date -Format "o"
        }
        
        if ($isDirty) {
            Write-Log "Health check: Git working directory is dirty" "WARN"
        }
        
        if (-not $networkOk) {
            Write-Log "Health check: Network connectivity issue" "WARN"
        }
        
        if ($freeSpaceGB -lt 10) {
            Write-Log "Health check: Low disk space ($freeSpaceGB GB)" "WARN"
        }
        
        # Store health status
        $healthPath = "D:\tmp\lantern-os\data\automation\health-status.json"
        $health | ConvertTo-Json -Depth 10 | Set-Content $healthPath
        
        Write-Log "Health check completed"
        return $health
    }
    finally {
        Pop-Location
    }
}

function Run-ComponentSequence {
    param(
        [array]$Components,
        [bool]$DryRun
    )
    
    # Sort by priority
    $sortedComponents = $Components | Sort-Object -Property priority
    
    $results = @{}
    
    foreach ($component in $sortedComponents) {
        Write-Log "Processing component: $($component.name)"
        $success = Invoke-Component -Component $component -DryRun $DryRun
        $results[$component.name] = @{
            success = $success
            timestamp = Get-Date -Format "o"
        }
        
        # If a high-priority component fails, stop the sequence
        if (-not $success -and $component.priority -le 2) {
            Write-Log "Critical component failed, stopping sequence" "ERROR"
            break
        }
    }
    
    return $results
}

function Send-Notification {
    param(
        [hashtable]$Results,
        [object]$Config
    )
    
    # Placeholder for notification logic
    Write-Log "Notification system not configured"
}

# Main execution
Write-Log "=== Automation Orchestrator Started ==="

$config = Get-OrchestratorConfig -ConfigFile $ConfigPath
if (-not $config) {
    Write-Log "Failed to load configuration" "ERROR"
    exit 1
}

Write-Log "Loaded configuration with $($config.components.Count) components"

$healthCheckCounter = 0

do {
    # Run health check periodically
    $healthCheckCounter++
    if ($healthCheckCounter -ge 30 / 10) {
        Run-HealthCheck
        $healthCheckCounter = 0
    }
    
    # Run component sequence
    Write-Log "Starting component sequence"
    $results = Run-ComponentSequence -Components $config.components -DryRun $DryRun
    
    # Store results
    $resultsPath = "D:\tmp\lantern-os\data\automation\orchestrator-results.json"
    $runResults = @{
        timestamp = Get-Date -Format "o"
        components = $results
        dryRun = $DryRun
    }
    $runResults | ConvertTo-Json -Depth 10 | Set-Content $resultsPath
    
    # Send notifications if configured
    Send-Notification -Results $results -Config $config
    
    # Check if all components succeeded
    $allSuccess = ($results.Values | Where-Object { -not $_.success }).Count -eq 0
    if ($allSuccess) {
        Write-Log "All components succeeded"
    } else {
        $failedCount = ($results.Values | Where-Object { -not $_.success }).Count
        Write-Log "$failedCount component(s) failed" "WARN"
    }
    
    if ($RunOnce) {
        break
    }
    
    # Wait for next cycle
    Write-Log "Next cycle in 10 minutes"
    Start-Sleep -Seconds (10 * 60)
    
} while ($true -and -not $RunOnce)

Write-Log "=== Automation Orchestrator Completed ==="