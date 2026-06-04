[CmdletBinding()]
param(
    [string]$AgentsConfigPath = "",
    [string]$ProjectsConfigPath = "",
    [string]$ProjectName = "",
    [string]$ProjectRepoPath = "",
    [string]$SlotName = "",
    [string]$ClaimedTaskRelativePath = "",
    [switch]$PrepareOnly,
    [switch]$RunOnce,
    [switch]$Headless,
    [switch]$Supervised
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Orch {
    param([string]$Message)
    if (-not $Headless) {
        Write-Host $Message
    }
}

function Read-Json {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        throw "Missing config file: $Path. Run scripts\Initialize-LocalConfig.ps1 first."
    }

    return Get-Content $Path -Raw | ConvertFrom-Json
}

function Resolve-OrchestratorPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,

        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }

    return (Join-Path $Root $Path)
}

function ConvertTo-Base64Json {
    param([Parameter(Mandatory = $true)]$Value)

    $json = $Value | ConvertTo-Json -Depth 30 -Compress
    return [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
}

function ConvertTo-SafeFileName {
    param([Parameter(Mandatory = $true)][string]$Value)
    return ($Value -replace "[^A-Za-z0-9._-]", "_")
}

function New-SupervisedLaunchLog {
    param(
        [Parameter(Mandatory = $true)][string]$Slot,
        [Parameter(Mandatory = $true)][string]$Kind
    )

    $dir = Join-Path $root "logs\control-actions\slot-launch"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $safeSlot = ConvertTo-SafeFileName -Value $Slot
    return Join-Path $dir ("{0}-{1}-{2}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $safeSlot, $Kind)
}

function Write-SupervisedLaunchAudit {
    param([object]$Payload)

    $dir = Join-Path $root "logs\control-actions"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $path = Join-Path $dir ("{0}-supervised_slot_launch-{1}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"), (ConvertTo-SafeFileName -Value ([string]$Payload.slot)))
    $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

$root = (Resolve-Path "$PSScriptRoot\..").Path

if ([string]::IsNullOrWhiteSpace($AgentsConfigPath)) {
    $AgentsConfigPath = Join-Path $root "config\agents.json"
}
else {
    $AgentsConfigPath = Resolve-OrchestratorPath -Root $root -Path $AgentsConfigPath
}

if ([string]::IsNullOrWhiteSpace($ProjectsConfigPath)) {
    $ProjectsConfigPath = Join-Path $root "config\projects.json"
}
else {
    $ProjectsConfigPath = Resolve-OrchestratorPath -Root $root -Path $ProjectsConfigPath
}

$agents = Read-Json $AgentsConfigPath
$projects = Read-Json $ProjectsConfigPath

if (-not [string]::IsNullOrWhiteSpace($ProjectRepoPath)) {
    $resolvedProjectRepoPath = Resolve-OrchestratorPath -Root $root -Path $ProjectRepoPath
    if (!(Test-Path $resolvedProjectRepoPath)) {
        throw "Project repo path not found: $resolvedProjectRepoPath"
    }

    if ([string]::IsNullOrWhiteSpace($ProjectName)) {
        $ProjectName = "orchestrator-bound-project"
    }

    $project = [pscustomobject]@{
        name = $ProjectName
        repoPath = $resolvedProjectRepoPath
        profilePath = $null
    }
}
else {
    if ([string]::IsNullOrWhiteSpace($ProjectName)) {
        $ProjectName = $projects.defaultProject
    }

    $project = $projects.projects | Where-Object { $_.name -eq $ProjectName } | Select-Object -First 1
    if ($null -eq $project) {
        throw "Project not found in config: $ProjectName"
    }

    if (!(Test-Path $project.repoPath)) {
        throw "Project repo path not found: $($project.repoPath)"
    }
}

$worktreeRoot = $projects.worktreeRoot
New-Item -ItemType Directory -Force -Path $worktreeRoot | Out-Null

Write-Orch "gm-agent-orchestrator"
Write-Orch "Root: $root"
Write-Orch "Agents config: $AgentsConfigPath"
Write-Orch "Projects config: $ProjectsConfigPath"
Write-Orch "Project: $($project.name)"
Write-Orch "Repo: $($project.repoPath)"
Write-Orch "Worktrees: $worktreeRoot"
Write-Orch "Supervised: $([bool]$Supervised)"

$startedCount = 0
$supervisedResults = @()

foreach ($slot in $agents.slots) {
    if (-not [string]::IsNullOrWhiteSpace($SlotName) -and $slot.name -ne $SlotName) {
        Write-Orch "Skipping non-selected slot: $($slot.name)"
        continue
    }

    if (-not $slot.enabled) {
        Write-Orch "Skipping disabled slot: $($slot.name)"
        continue
    }

    $worktreePath = Join-Path $worktreeRoot $slot.name
    $worktreePrepOutput = @()

    $worktreePrepOutput = @(& "$PSScriptRoot\New-AgentWorktree.ps1" `
        -ProjectRepo $project.repoPath `
        -WorktreePath $worktreePath `
        -Branch $slot.branch 2>&1 | ForEach-Object { $_.ToString() })

    if (-not $Headless) {
        foreach ($line in $worktreePrepOutput) {
            if (-not [string]::IsNullOrWhiteSpace($line)) { Write-Orch $line }
        }
    }

    Write-Orch "Prepared slot: $($slot.name)"

    if ($PrepareOnly) {
        continue
    }

    $slotJsonBase64 = ConvertTo-Base64Json -Value $slot
    $projectJsonBase64 = ConvertTo-Base64Json -Value $project

    $slotArgs = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSScriptRoot\Start-AgentSlot.ps1`"",
        "-OrchestratorRoot", "`"$root`"",
        "-WorktreePath", "`"$worktreePath`"",
        "-SlotJsonBase64", $slotJsonBase64,
        "-ProjectJsonBase64", $projectJsonBase64,
        "-FallbackWaitMinutes", "$($agents.fallbackWaitMinutes)",
        "-MaxResumeCycles", "$($agents.maxResumeCycles)"
    )

    if (-not [string]::IsNullOrWhiteSpace($ClaimedTaskRelativePath)) {
        $slotArgs += @("-ClaimedTaskRelativePath", "$ClaimedTaskRelativePath")
    }

    if ($RunOnce) {
        $slotArgs += "-RunOnce"
    }

    if ($Headless) {
        $slotArgs += "-Headless"
    }

    $commandLine = "powershell.exe " + ($slotArgs -join " ")
    $stdoutPath = ""
    $stderrPath = ""
    $auditPath = ""
    $exitCode = $null

    if ($Supervised) {
        $stdoutPath = New-SupervisedLaunchLog -Slot ([string]$slot.name) -Kind "stdout"
        $stderrPath = New-SupervisedLaunchLog -Slot ([string]$slot.name) -Kind "stderr"

        $process = Start-Process powershell.exe `
            -ArgumentList $slotArgs `
            -WorkingDirectory $root `
            -PassThru `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath

        if ($RunOnce) {
            $process.WaitForExit()
            $exitCode = $process.ExitCode
        }

        $auditPayload = [pscustomobject]@{
            ok = $true
            mode = "supervised"
            slot = [string]$slot.name
            processId = $process.Id
            exitCode = $exitCode
            runOnce = [bool]$RunOnce
            headless = [bool]$Headless
            commandLine = $commandLine
            stdoutPath = $stdoutPath.Replace($root, "").TrimStart("\")
            stderrPath = $stderrPath.Replace($root, "").TrimStart("\")
            worktreePath = $worktreePath
            worktreePrepOutput = @($worktreePrepOutput)
            generatedAt = (Get-Date).ToString("o")
        }
        $auditPath = Write-SupervisedLaunchAudit -Payload $auditPayload
        $supervisedResults += $auditPayload | Add-Member -PassThru -NotePropertyName auditPath -NotePropertyValue $auditPath
    }
    elseif ($Headless) {
        Start-Process powershell.exe -ArgumentList $slotArgs -WindowStyle Hidden -WorkingDirectory $root
    }
    else {
        Start-Process powershell.exe -ArgumentList $slotArgs -WorkingDirectory $root
    }
    $startedCount++

    Write-Orch "Started slot: $($slot.name)"
    if ($Supervised) {
        Write-Orch "  PID: $($supervisedResults[-1].processId)"
        Write-Orch "  ExitCode: $($supervisedResults[-1].exitCode)"
        Write-Orch "  Stdout: $stdoutPath"
        Write-Orch "  Stderr: $stderrPath"
        Write-Orch "  Audit: $auditPath"
    }
}

if (-not $PrepareOnly -and $startedCount -eq 0) {
    if ([string]::IsNullOrWhiteSpace($SlotName)) {
        throw "No enabled agent slots were started. Check config\agents.json."
    }

    throw "No enabled agent slot matched SlotName: $SlotName"
}

if ($Supervised) {
    [pscustomobject]@{
        ok = $true
        mode = "supervised"
        root = $root
        startedCount = $startedCount
        results = @($supervisedResults)
        generatedAt = (Get-Date).ToString("o")
    } | ConvertTo-Json -Depth 30
}
