[CmdletBinding()]
param(
    [ValidateSet("all", "claude", "codex")]
    [string]$Agent = "all",

    [string]$OrchestratorRoot = (Resolve-Path "$PSScriptRoot\..").Path,

    [switch]$LaunchClaudeInteractive,

    [switch]$LaunchCodexInteractive,

    [int]$SmokeTimeoutSeconds = 45,

    [switch]$JsonOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (!(Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Invoke-CommandSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = "",
        [int]$TimeoutSeconds = 30
    )

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("gm-agent-orchestrator-{0}" -f ([Guid]::NewGuid().ToString("N")))
    Ensure-Directory -Path $tempRoot
    $stdoutPath = Join-Path $tempRoot "stdout.log"
    $stderrPath = Join-Path $tempRoot "stderr.log"

    try {
        $startInfo = @{
            FilePath = $Executable
            ArgumentList = $Arguments
            RedirectStandardOutput = $stdoutPath
            RedirectStandardError = $stderrPath
            NoNewWindow = $true
            PassThru = $true
        }
        if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
            $startInfo.WorkingDirectory = $WorkingDirectory
        }

        $process = Start-Process @startInfo
        $finished = $process.WaitForExit($TimeoutSeconds * 1000)
        if (-not $finished) {
            try { $process.Kill() } catch { }
            return [pscustomobject]@{
                ok = $false
                exitCode = -2
                timedOut = $true
                output = @("Command timed out after $TimeoutSeconds seconds.")
                stderr = @()
            }
        }

        $stdout = @()
        $stderr = @()
        if (Test-Path -LiteralPath $stdoutPath) { $stdout = @(Get-Content -LiteralPath $stdoutPath -ErrorAction SilentlyContinue) }
        if (Test-Path -LiteralPath $stderrPath) { $stderr = @(Get-Content -LiteralPath $stderrPath -ErrorAction SilentlyContinue) }

        return [pscustomobject]@{
            ok = ($process.ExitCode -eq 0)
            exitCode = [int]$process.ExitCode
            timedOut = $false
            output = @($stdout | ForEach-Object { $_.ToString() })
            stderr = @($stderr | ForEach-Object { $_.ToString() })
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            exitCode = -1
            timedOut = $false
            output = @($_.Exception.Message)
            stderr = @()
        }
    }
    finally {
        try { Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue } catch { }
    }
}

function Test-Executable {
    param([Parameter(Mandatory = $true)][string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        return [pscustomobject]@{
            name = $Name
            found = $false
            path = ""
            version = $null
        }
    }

    $version = Invoke-CommandSafe -Executable $Name -Arguments @("--version") -WorkingDirectory $root -TimeoutSeconds 20
    return [pscustomobject]@{
        name = $Name
        found = $true
        path = $cmd.Source
        version = $version
    }
}

$root = (Resolve-Path -LiteralPath $OrchestratorRoot).Path
$statusDir = Join-Path $root "status"
$reportDir = Join-Path $root "reports\audit"
Ensure-Directory -Path $statusDir
Ensure-Directory -Path $reportDir

$agentsToCheck = @()
if ($Agent -eq "all" -or $Agent -eq "claude") { $agentsToCheck += "claude" }
if ($Agent -eq "all" -or $Agent -eq "codex") { $agentsToCheck += "codex" }

$toolChecks = @()
$toolChecks += Test-Executable -Name "git"
$toolChecks += Test-Executable -Name "gh"
foreach ($agentName in $agentsToCheck) {
    $toolChecks += Test-Executable -Name $agentName
}

$gitStatus = Invoke-CommandSafe -Executable "git" -Arguments @("status", "-sb") -WorkingDirectory $root -TimeoutSeconds 20
$ghAuth = Invoke-CommandSafe -Executable "gh" -Arguments @("auth", "status") -WorkingDirectory $root -TimeoutSeconds 20

$agentSmoke = @()
if ($agentsToCheck -contains "claude") {
    $claudeFound = ($toolChecks | Where-Object { $_.name -eq "claude" } | Select-Object -First 1).found
    if ($claudeFound) {
        $agentSmoke += [pscustomobject]@{
            agent = "claude"
            command = "claude --print"
            result = Invoke-CommandSafe -Executable "claude" -Arguments @("--print", "Return exactly CLAUDE_READY.") -WorkingDirectory $root -TimeoutSeconds $SmokeTimeoutSeconds
        }
    }
}

if ($agentsToCheck -contains "codex") {
    $codexFound = ($toolChecks | Where-Object { $_.name -eq "codex" } | Select-Object -First 1).found
    if ($codexFound) {
        $agentSmoke += [pscustomobject]@{
            agent = "codex"
            command = "codex --version"
            result = Invoke-CommandSafe -Executable "codex" -Arguments @("--version") -WorkingDirectory $root -TimeoutSeconds 20
        }
    }
}

$launched = @()
if ($LaunchClaudeInteractive) {
    $claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
    if ($null -ne $claudeCmd) {
        Start-Process powershell.exe -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            "Set-Location -LiteralPath '$root'; Write-Host 'Claude opened in orchestrator root. If Claude asks to trust/init this folder, approve it once. If needed, run /init inside Claude, then exit.' -ForegroundColor Cyan; claude"
        )
        $launched += "claude interactive shell in orchestrator root"
    }
}

if ($LaunchCodexInteractive) {
    $codexCmd = Get-Command codex -ErrorAction SilentlyContinue
    if ($null -ne $codexCmd) {
        Start-Process powershell.exe -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            "Set-Location -LiteralPath '$root'; Write-Host 'Codex opened in orchestrator root. Complete any local auth/trust prompt once, then exit.' -ForegroundColor Cyan; codex"
        )
        $launched += "codex interactive shell in orchestrator root"
    }
}

$blockers = @()
foreach ($check in $toolChecks) {
    if (-not $check.found) { $blockers += ("Missing executable on PATH: {0}" -f $check.name) }
}
if (-not $ghAuth.ok) { $blockers += "gh auth status failed; GitHub issue updates may not work locally." }
foreach ($smoke in $agentSmoke) {
    if (-not $smoke.result.ok) { $blockers += ("{0} smoke check failed or timed out." -f $smoke.agent) }
}

$result = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    orchestratorRoot = $root
    requestedAgent = $Agent
    toolChecks = $toolChecks
    gitStatus = $gitStatus
    ghAuth = $ghAuth
    agentSmoke = $agentSmoke
    launched = $launched
    blockers = $blockers
    ok = ($blockers.Count -eq 0)
    note = "Interactive init is only launched when requested. Secrets and one-time approvals stay local and are not captured."
}

$jsonPath = Join-Path $statusDir "agent-cli-init.json"
$result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$reportPath = Join-Path $reportDir ((Get-Date -Format "yyyyMMdd-HHmmss") + "-agent-cli-init.md")
$lines = @()
$lines += "# Agent CLI Init Audit"
$lines += ""
$lines += ("Generated: {0}" -f $result.generatedAt)
$lines += ("Root: {0}" -f $root)
$lines += ("Requested agent: {0}" -f $Agent)
$lines += ("Overall ok: {0}" -f $result.ok)
$lines += ""
$lines += "## Tools"
$lines += ""
foreach ($check in $toolChecks) {
    $lines += ("- {0}: found={1} path={2}" -f $check.name, $check.found, $check.path)
}
$lines += ""
$lines += "## Smoke checks"
$lines += ""
if ($agentSmoke.Count -eq 0) { $lines += "No agent smoke checks were run." }
foreach ($smoke in $agentSmoke) {
    $lines += ("- {0}: ok={1} exit={2} timedOut={3}" -f $smoke.agent, $smoke.result.ok, $smoke.result.exitCode, $smoke.result.timedOut)
}
$lines += ""
$lines += "## Launched"
$lines += ""
if ($launched.Count -eq 0) { $lines += "No interactive CLI was launched." }
foreach ($item in $launched) { $lines += ("- {0}" -f $item) }
$lines += ""
$lines += "## Blockers"
$lines += ""
if ($blockers.Count -eq 0) { $lines += "No blockers detected." }
foreach ($blocker in $blockers) { $lines += ("- {0}" -f $blocker) }
$lines | Set-Content -LiteralPath $reportPath -Encoding UTF8

if ($JsonOnly) {
    $result | ConvertTo-Json -Depth 20
}
else {
    Write-Host "Agent CLI init audit complete." -ForegroundColor Green
    Write-Host "JSON: $jsonPath"
    Write-Host "Report: $reportPath"
    if ($blockers.Count -gt 0) {
        Write-Host "Blockers detected: $($blockers.Count)" -ForegroundColor Yellow
    }
    if ($launched.Count -gt 0) {
        Write-Host "Interactive shells launched: $($launched -join ', ')" -ForegroundColor Cyan
    }
}
