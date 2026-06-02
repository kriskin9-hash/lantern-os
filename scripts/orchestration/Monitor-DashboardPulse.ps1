[CmdletBinding()]
param(
    [int]$IntervalSeconds = 60,
    [string]$DashboardUrl = "http://localhost:8765/api/status",
    [int]$ServerRetryCount = 3,
    [int]$ServerRetryDelayMs = 2000,
    [switch]$Headless
)

$notifyIcon = $null
if (-not $Headless) {
    Add-Type -AssemblyName System.Windows.Forms
    $notifyIcon = New-Object System.Windows.Forms.NotifyIcon
    $notifyIcon.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon((Get-Process -Id $PID).Path)
    $notifyIcon.Visible = $true
}

$statusPath = Join-Path $PSScriptRoot "..\status\orchestrator.json"
$lastState = ""
$lastHeadline = ""
$lastAgentStates = @{} 
$lastServerOnline = $true

Write-Host "Monitoring dashboard pulse every $IntervalSeconds seconds..."
Write-Host "Server Retry: $ServerRetryCount attempts with $($ServerRetryDelayMs)ms delay"

function Send-Notification {
    param($Title, $Message, $State)
    if ($null -eq $notifyIcon) {
        # Headless mode: skip UI notification but log to console
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [STATE CHANGE] $Title - $Message"
        return
    }
    $tipIcon = [System.Windows.Forms.ToolTipIcon]::Info
    if ($State -eq "needs_attention" -or $State -eq "blocked" -or $State -eq "sleeping") {
        $tipIcon = [System.Windows.Forms.ToolTipIcon]::Warning
    } elseif ($State -eq "failed" -or $State -eq "offline") {
        $tipIcon = [System.Windows.Forms.ToolTipIcon]::Error
    }
    $notifyIcon.ShowBalloonTip(10000, $Title, $Message, $tipIcon)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Notification sent: $Title - $Message"
}

function Test-ServerPulse {
    for ($i = 1; $i -le $ServerRetryCount; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $DashboardUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { return $true }
        } catch {
            if ($i -lt $ServerRetryCount) {
                Start-Sleep -Milliseconds $ServerRetryDelayMs
            }
        }
    }
    return $false
}

try {
    while ($true) {
        $serverOnline = Test-ServerPulse

        # Server status change - only notify if it transitions to offline after retries
        if ($serverOnline -ne $lastServerOnline) {
            if (-not $serverOnline) {
                Send-Notification "Dashboard Offline" "The dashboard server at $DashboardUrl is persistentley unreachable." "offline"
            } else {
                Send-Notification "Dashboard Online" "The dashboard server is back online." "online"
            }
            $lastServerOnline = $serverOnline
        }

        if (Test-Path $statusPath) {
            try {
                $status = Get-Content $statusPath -Raw | ConvertFrom-Json
                
                # Global Orchestrator Change
                $currentState = $status.state
                $currentHeadline = $status.headline
                if ($currentState -ne $lastState -or $currentHeadline -ne $lastHeadline) {
                    Send-Notification "Orchestrator: $currentState" $currentHeadline $currentState
                    $lastState = $currentState
                    $lastHeadline = $currentHeadline
                }

                # Individual Agent Changes
                if ($null -ne $status.slots) {
                    foreach ($slot in $status.slots) {
                        $name = $slot.name
                        $state = $slot.state
                        $statusText = $slot.statusText

                        if (-not $lastAgentStates.ContainsKey($name)) {
                            $lastAgentStates[$name] = $state
                        } elseif ($lastAgentStates[$name] -ne $state) {
                            Send-Notification "Agent: $name -> $state" $statusText $state
                            $lastAgentStates[$name] = $state
                        }
                    }
                }
            }
            catch {
                # Don't notify on parse errors unless they persist (could be a write-lock race)
                Write-Warning "Failed to parse orchestrator status: $($_.Exception.Message)"
            }
        }

        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    if ($null -ne $notifyIcon) {
        $notifyIcon.Visible = $false
        $notifyIcon.Dispose()
    }
}
