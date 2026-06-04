[CmdletBinding()]
param(
    [int]$Port = 8765,
    [switch]$NoOpen,
    [switch]$NoRefresh,
    [switch]$Force,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-IsAdministrator {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = [Security.Principal.WindowsPrincipal]::new($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch {
        return $false
    }
}

function New-Result {
    param(
        [string]$State,
        [string]$Message,
        [int]$Port,
        [int[]]$StoppedProcessIds = @(),
        [int]$StartedProcessId = 0,
        [object[]]$Listeners = @(),
        [object[]]$DashboardProcesses = @()
    )

    [pscustomobject]@{
        state = $State
        message = $Message
        port = $Port
        stoppedProcessIds = @($StoppedProcessIds)
        startedProcessId = $StartedProcessId
        listeners = @($Listeners)
        dashboardProcesses = @($DashboardProcesses)
        timestamp = (Get-Date).ToString('o')
    }
}

function Write-ResultAndExit {
    param(
        [object]$Result,
        [int]$ExitCode
    )

    if ($Json) {
        $Result | ConvertTo-Json -Depth 8
    }
    else {
        Write-Host ("{0}: {1}" -f $Result.state, $Result.message)
        if ($Result.stoppedProcessIds.Count -gt 0) {
            Write-Host ("Stopped PID(s): {0}" -f ($Result.stoppedProcessIds -join ', '))
        }
        if ($Result.startedProcessId -gt 0) {
            Write-Host ("Started PID: {0}" -f $Result.startedProcessId)
        }
    }

    exit $ExitCode
}

function Get-ProcessCommandLine {
    param([int]$ProcessId)

    try {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
        return [string]$process.CommandLine
    }
    catch {
        return ''
    }
}

function Get-DashboardProcesses {
    param([string]$RepoRoot)

    $escapedRoot = [Regex]::Escape($RepoRoot)
    return @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match $escapedRoot -and
            $_.CommandLine -match 'Start-Dashboard\.ps1'
        } |
        ForEach-Object {
            [pscustomobject]@{
                processId = [int]$_.ProcessId
                commandLine = [string]$_.CommandLine
            }
        })
}

function Get-PortListeners {
    param([int]$Port)

    return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
        $owningProcessId = [int]$_.OwningProcess
        [pscustomobject]@{
            localAddress = [string]$_.LocalAddress
            localPort = [int]$_.LocalPort
            owningProcess = $owningProcessId
            commandLine = Get-ProcessCommandLine -ProcessId $owningProcessId
        }
    })
}

function Resolve-PowerShellCommandPath {
    $pwshCommand = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($null -ne $pwshCommand -and -not [string]::IsNullOrWhiteSpace([string]$pwshCommand.Source)) {
        return [string]$pwshCommand.Source
    }

    $windowsPowerShellCommand = Get-Command powershell -ErrorAction Stop
    if ($null -eq $windowsPowerShellCommand -or [string]::IsNullOrWhiteSpace([string]$windowsPowerShellCommand.Source)) {
        throw 'Could not resolve a PowerShell executable path.'
    }

    return [string]$windowsPowerShellCommand.Source
}

if (-not (Test-IsAdministrator)) {
    $result = New-Result -State 'blocked' -Message 'Restart-DashboardServer.ps1 must be run from an elevated PowerShell session.' -Port $Port
    Write-ResultAndExit -Result $result -ExitCode 2
}

$root = (Resolve-Path "$PSScriptRoot\..").Path
$startScript = Join-Path $PSScriptRoot 'Start-Dashboard.ps1'
if (-not (Test-Path $startScript)) {
    $result = New-Result -State 'failed' -Message "Start script was not found: $startScript" -Port $Port
    Write-ResultAndExit -Result $result -ExitCode 1
}

$stopped = New-Object System.Collections.Generic.List[int]
$initialListeners = @(Get-PortListeners -Port $Port)
$dashboardProcesses = @(Get-DashboardProcesses -RepoRoot $root)

foreach ($dashboardProcess in $dashboardProcesses) {
    Stop-Process -Id $dashboardProcess.processId -Force -ErrorAction Stop
    $stopped.Add([int]$dashboardProcess.processId)
}

if ($dashboardProcesses.Count -gt 0) {
    Start-Sleep -Seconds 1
}

$remainingListeners = @(Get-PortListeners -Port $Port)
if ($remainingListeners.Count -gt 0) {
    $unknownListeners = @($remainingListeners | Where-Object { $_.owningProcess -ne 4 })
    if ($unknownListeners.Count -gt 0) {
        $result = New-Result -State 'blocked' -Message "Port $Port is owned by a non-dashboard process. Refusing to stop it." -Port $Port -StoppedProcessIds $stopped.ToArray() -Listeners $remainingListeners -DashboardProcesses $dashboardProcesses
        Write-ResultAndExit -Result $result -ExitCode 4
    }

    if ($dashboardProcesses.Count -eq 0) {
        $result = New-Result -State 'blocked' -Message "Port $Port is owned by HTTP.sys/System (PID 4), and no orchestrator Start-Dashboard.ps1 process was found to bounce. Clear the startup registration or choose a different port." -Port $Port -StoppedProcessIds $stopped.ToArray() -Listeners $remainingListeners -DashboardProcesses $dashboardProcesses
        Write-ResultAndExit -Result $result -ExitCode 3
    }

    $result = New-Result -State 'blocked' -Message "Stopped dashboard process(es), but port $Port is still held by HTTP.sys/System. A non-process URL reservation or service registration still owns the prefix." -Port $Port -StoppedProcessIds $stopped.ToArray() -Listeners $remainingListeners -DashboardProcesses $dashboardProcesses
    Write-ResultAndExit -Result $result -ExitCode 5
}

$powerShell = Resolve-PowerShellCommandPath

$argumentList = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $startScript,
    '-Port', [string]$Port
)
if ($NoOpen) { $argumentList += '-NoOpen' }
if ($NoRefresh) { $argumentList += '-NoRefresh' }

$process = Start-Process -FilePath $powerShell -WorkingDirectory $root -ArgumentList $argumentList -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 2

$startedListeners = @(Get-PortListeners -Port $Port)
if ($startedListeners.Count -eq 0) {
    $result = New-Result -State 'failed' -Message "Dashboard server process was started, but port $Port is not listening yet." -Port $Port -StoppedProcessIds $stopped.ToArray() -StartedProcessId $process.Id -Listeners $initialListeners -DashboardProcesses $dashboardProcesses
    Write-ResultAndExit -Result $result -ExitCode 6
}

$result = New-Result -State 'succeeded' -Message "Dashboard server is listening on http://localhost:$Port/." -Port $Port -StoppedProcessIds $stopped.ToArray() -StartedProcessId $process.Id -Listeners $startedListeners -DashboardProcesses $dashboardProcesses
Write-ResultAndExit -Result $result -ExitCode 0
