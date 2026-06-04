<#
.SYNOPSIS
Run an allowlisted orchestrator PowerShell helper and return audited JSON.

.DESCRIPTION
Provides a constrained local execution surface for MCP/connector wrappers. It is
not a generic shell. Callers choose one script from a fixed allowlist and pass
arguments to that script. Every allowed or rejected invocation writes an audit
record under logs/control-actions.

Prior work considered:
- scripts/Invoke-OrchestratorPowerShellPatch.ps1 provides staged file patch
  promotion/rollback, but it does not run existing operational helpers.
- scripts/New-OrchestratorQueueTask.ps1, scripts/Get-OrchestratorStatus.ps1,
  scripts/Invoke-OrchestratorTaskAction.ps1, and repo/status helpers already
  provide bounded operations, but they lacked one audited MCP-facing runner.
- Issue #215 defines the broader MCP repair-surface gap, but this script is the
  narrow allowlisted helper runner instead of a general shell.

.PARAMETER ScriptName
Basename of the allowed helper script to run.

.PARAMETER RunnerArguments
Arguments passed to the helper script when invoking from PowerShell with
splatting or a prebuilt string array.

.PARAMETER ArgumentJson
JSON array of helper arguments. Useful when the caller invokes this script in-process.

.PARAMETER ArgumentJsonBase64
UTF-8 base64 encoded JSON array of helper arguments. Prefer this for MCP and
powershell.exe -File calls because it avoids command-line quote mangling.

.PARAMETER Root
Repository root. Defaults to the parent directory of this script.

.PARAMETER DryRun
Append -DryRun for helpers that support it, unless already present.

.PARAMETER PlanOnly
Append -PlanOnly for helpers that support it, unless already present.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ScriptName,

    [Parameter()]
    [string[]]$RunnerArguments = @(),

    [Parameter()]
    [string]$ArgumentJson = "",

    [Parameter()]
    [string]$ArgumentJsonBase64 = "",

    [Parameter()]
    [string]$Root = "",

    [Parameter()]
    [switch]$DryRun,

    [Parameter()]
    [switch]$PlanOnly,

    [Parameter()]
    [int]$TimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}
$Root = [System.IO.Path]::GetFullPath($Root)

function Test-PathUnderRoot {
    param(
        [string]$Candidate,
        [string]$BaseRoot
    )

    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $false }
    if ([string]::IsNullOrWhiteSpace($BaseRoot)) { return $false }

    $baseFull = [System.IO.Path]::GetFullPath($BaseRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $candidateFull = [System.IO.Path]::GetFullPath($Candidate)
    $baseWithSeparator = $baseFull + [System.IO.Path]::DirectorySeparatorChar

    return [string]::Equals($candidateFull, $baseFull, [System.StringComparison]::OrdinalIgnoreCase) -or
        $candidateFull.StartsWith($baseWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-RelativePath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    if (Test-PathUnderRoot -Candidate $pathFull -BaseRoot $rootFull) {
        return $pathFull.Substring($rootFull.Length).TrimStart("\", "/") -replace "\\", "/"
    }
    return $pathFull
}

function Get-AllowedScripts {
    $entries = @(
        @{ name = "Get-OrchestratorStatus.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "status" },
        @{ name = "Get-OrchMcpCapabilityStatus.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "status" },
        @{ name = "Get-GitStatusShort.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "status" },
        @{ name = "New-OrchestratorQueueTask.ps1"; relPath = "scripts"; mutates = $true; dryRun = $true; planOnly = $false; category = "queue" },
        @{ name = "Invoke-OrchestratorTaskAction.ps1"; relPath = "scripts"; mutates = $true; dryRun = $true; planOnly = $false; category = "task-action" },
        @{ name = "Invoke-OrchestratorAgentAction.ps1"; relPath = "scripts"; mutates = $true; dryRun = $true; planOnly = $false; category = "agent-action" },
        @{ name = "Invoke-OrchestratorRepoSync.ps1"; relPath = "scripts"; mutates = $true; dryRun = $true; planOnly = $true; category = "repo-sync" },
        @{ name = "Get-GitHubDataCache.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "cache" },
        @{ name = "Test-OrchestratorStatusJson.ps1"; relPath = "tests"; mutates = $false; dryRun = $false; planOnly = $false; category = "validation" },
        @{ name = "Test-OrchMcpServerContracts.ps1"; relPath = "tests"; mutates = $false; dryRun = $false; planOnly = $false; category = "validation" },
        @{ name = "Get-GameMakerProjectInfo.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "build-status" },
        @{ name = "Get-GameMakerCompilerErrors.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "build-status" },
        @{ name = "Get-GameMakerSpriteAssetStatus.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "build-status" },
        @{ name = "Get-GameMakerRoomEditorStatus.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "build-status" },
        @{ name = "Get-GameMakerBuildStatus.ps1"; relPath = "scripts"; mutates = $false; dryRun = $false; planOnly = $false; category = "build-status" }
    )

    $map = @{}
    foreach ($entry in $entries) {
        $map[$entry.name.ToLowerInvariant()] = [pscustomobject]@{
            name = [string]$entry.name
            relativeDirectory = [string]$(if ($entry.relPath) { $entry.relPath } else { "scripts" })
            mutatesByDefault = [bool]$entry.mutates
            supportsDryRun = [bool]$entry.dryRun
            supportsPlanOnly = [bool]$entry.planOnly
            category = [string]$entry.category
        }
    }
    return $map
}

function ConvertFrom-ArgumentJsonBase64 {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    try {
        $bytes = [System.Convert]::FromBase64String($Value)
        return [System.Text.Encoding]::UTF8.GetString($bytes)
    }
    catch {
        throw "ArgumentJsonBase64 must be valid UTF-8 base64 encoded JSON: $($_.Exception.Message)"
    }
}

function ConvertFrom-ArgumentJson {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return @() }
    $normalized = $Value
    # Compatibility for callers that double-escape JSON quotes, e.g. [\"-Root\",\".\"]
    if ($normalized -match '\\\"') {
        $normalized = $normalized -replace '\\\"', '"'
    }
    try {
        $parsed = $normalized | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        # Compatibility path: some callers send a comma-separated JSON fragment without []
        # e.g. "-Root",".". Auto-wrap once before failing hard.
        $trimmed = $normalized.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmed) -and $trimmed -notmatch '^\[') {
            try {
                $parsed = ("[{0}]" -f $trimmed) | ConvertFrom-Json -ErrorAction Stop
            }
            catch {
                # Legacy compatibility: accept raw comma-separated scalar tokens
                # like -Root,. or "-Root","." and coerce to a string array.
                $parts = @($trimmed -split ",")
                if ($parts.Count -gt 0) {
                    $legacy = @()
                    foreach ($part in $parts) {
                        $token = ([string]$part).Trim()
                        if ($token.Length -eq 0) { continue }
                        if (($token.StartsWith('"') -and $token.EndsWith('"')) -or ($token.StartsWith("'") -and $token.EndsWith("'"))) {
                            $token = $token.Substring(1, $token.Length - 2)
                        }
                        if ($token.Length -gt 0) { $legacy += $token }
                    }
                    if ($legacy.Count -gt 0) { return ,$legacy }
                }
                throw "ArgumentJson must be a JSON array of strings: $($_.Exception.Message)"
            }
        }
        else {
            throw "ArgumentJson must be a JSON array of strings: $($_.Exception.Message)"
        }
    }

    if ($null -eq $parsed) { return @() }
    $items = @($parsed)
    $result = @()
    foreach ($item in $items) {
        if ($null -eq $item) { throw "ArgumentJson must not contain null values." }
        if ($item -is [System.Array] -or $item -is [System.Collections.IDictionary]) { throw "ArgumentJson values must be scalar strings." }
        $result += [string]$item
    }
    return $result
}

function ConvertTo-ProcessArgument {
    param([AllowNull()][string]$Value)

    if ($null -eq $Value) { return '""' }
    if ($Value.Length -eq 0) { return '""' }
    if ($Value -notmatch '[\s"]') { return $Value }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $slashCount = 0
    foreach ($char in $Value.ToCharArray()) {
        if ($char -eq '\') {
            $slashCount++
            continue
        }

        if ($char -eq '"') {
            if ($slashCount -gt 0) { [void]$builder.Append('\' * ($slashCount * 2)) }
            [void]$builder.Append('\"')
            $slashCount = 0
            continue
        }

        if ($slashCount -gt 0) {
            [void]$builder.Append('\' * $slashCount)
            $slashCount = 0
        }
        [void]$builder.Append($char)
    }

    if ($slashCount -gt 0) { [void]$builder.Append('\' * ($slashCount * 2)) }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Test-SafeScriptName {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Missing script_name." }
    if ($Value -ne [System.IO.Path]::GetFileName($Value)) { throw "script_name must be a basename from the allowlist." }
    if ([System.IO.Path]::GetExtension($Value) -ne ".ps1") { throw "script_name must be an allowlisted .ps1 helper." }
    if ($Value -match "[\\/:*?`"<>|\x00]") { throw "script_name contains unsafe path characters." }
}

function Test-SafeArgument {
    param([string]$Value)

    if ($null -eq $Value) { return }
    if ($Value.Length -gt 20000) { throw "Runner argument exceeds 20000 characters." }
    if ($Value.IndexOf([char]0) -ge 0) { throw "Runner arguments must not contain NUL bytes." }
    if ($Value.IndexOf([char]10) -ge 0 -or $Value.IndexOf([char]13) -ge 0) { throw "Runner arguments must not contain CR or LF characters." }
    if ($Value -match "[\x01-\x08\x0B\x0C\x0E-\x1F]") { throw "Runner arguments contain unsupported control characters." }
}

function Test-ArgumentPresent {
    param([string[]]$Arguments, [string]$Name)

    foreach ($arg in @($Arguments)) {
        if ([string]::Equals([string]$arg, $Name, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Get-TailText {
    param([string]$Value, [int]$MaxChars = 12000)

    if ([string]::IsNullOrEmpty($Value)) { return "" }
    if ($Value.Length -le $MaxChars) { return $Value }
    return $Value.Substring($Value.Length - $MaxChars, $MaxChars)
}

function Write-AuditEvent {
    param([object]$Payload)

    $dir = Join-Path $Root "logs\control-actions"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
    $path = Join-Path $dir ("{0}-safe_powershell_runner.json" -f $stamp)
    $i = 0
    while (Test-Path $path) {
        $i++
        $path = Join-Path $dir ("{0}-{1}-safe_powershell_runner.json" -f $stamp, $i)
    }
    $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

function New-Result {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$Reason = "",
        [int]$ExitCode = -1,
        [string]$Command = "powershell",
        [string[]]$Args = @(),
        [string]$Stdout = "",
        [string]$Stderr = "",
        [bool]$MutatedState = $false,
        [object]$AllowedScript = $null
    )

    return [ordered]@{
        ok = [bool]$Ok
        action = "safe_powershell_runner"
        state = $State
        generatedAt = (Get-Date).ToUniversalTime().ToString("o")
        scriptName = $ScriptName
        allowed = ($null -ne $AllowedScript)
        category = $(if ($AllowedScript) { [string]$AllowedScript.category } else { "blocked" })
        command = $Command
        args = @($Args)
        exitCode = $ExitCode
        stdoutTail = Get-TailText -Value $Stdout
        stderrTail = Get-TailText -Value $Stderr
        auditPath = ""
        mutatedState = [bool]$MutatedState
        dryRun = [bool]$DryRun
        planOnly = [bool]$PlanOnly
        reason = $Reason
    }
}

$allowedScripts = Get-AllowedScripts
$result = $null
$auditPath = ""
$helperArguments = @()

try {
    Test-SafeScriptName -Value $ScriptName
    $helperArguments = @($RunnerArguments)
    if (-not [string]::IsNullOrWhiteSpace($ArgumentJsonBase64)) {
        $decodedJson = ConvertFrom-ArgumentJsonBase64 -Value $ArgumentJsonBase64
        $helperArguments = @(ConvertFrom-ArgumentJson -Value $decodedJson)
    }
    elseif (-not [string]::IsNullOrWhiteSpace($ArgumentJson)) {
        $helperArguments = @(ConvertFrom-ArgumentJson -Value $ArgumentJson)
    }
    foreach ($arg in @($helperArguments)) { Test-SafeArgument -Value $arg }

    $lookup = $ScriptName.ToLowerInvariant()
    if (-not $allowedScripts.ContainsKey($lookup)) {
        throw "Blocked unsafe command. Only orchestrator helper scripts on the safe runner allowlist may be executed."
    }

    $allowed = $allowedScripts[$lookup]
    $scriptsRoot = [System.IO.Path]::GetFullPath((Join-Path $Root $allowed.relativeDirectory)).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $scriptPath = [System.IO.Path]::GetFullPath((Join-Path $scriptsRoot $allowed.name))
    if (-not (Test-PathUnderRoot -Candidate $scriptPath -BaseRoot $scriptsRoot)) {
        throw "Resolved script path escaped the orchestrator scripts directory."
    }
    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
        throw "Allowed script was not found: $(Get-RelativePath -Path $scriptPath)"
    }

    $effectiveArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath) + @($helperArguments)
    if ($DryRun -and $allowed.supportsDryRun -and -not (Test-ArgumentPresent -Arguments $effectiveArgs -Name "-DryRun")) {
        $effectiveArgs += "-DryRun"
    }
    if ($PlanOnly -and $allowed.supportsPlanOnly -and -not (Test-ArgumentPresent -Arguments $effectiveArgs -Name "-PlanOnly")) {
        $effectiveArgs += "-PlanOnly"
    }

    $temp = [System.IO.Path]::GetTempFileName()
    $stdoutPath = "$temp.out"
    $stderrPath = "$temp.err"
    try {
        $argumentLine = ($effectiveArgs | ForEach-Object { ConvertTo-ProcessArgument -Value $_ }) -join " "
        $process = Start-Process -FilePath "powershell" -ArgumentList $argumentLine -WorkingDirectory $Root -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
        $finished = $process.WaitForExit([Math]::Max(1, $TimeoutSeconds) * 1000)
        if (-not $finished) {
            try { $process.Kill() } catch {}
        }

        $stdout = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -LiteralPath $stdoutPath -Raw } else { "" }
        $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw } else { "" }
        $exitCode = if ($finished) { [int]$process.ExitCode } else { -1 }
        $state = if ($finished -and $exitCode -eq 0) { "completed" } elseif (-not $finished) { "timeout" } else { "failed" }
        $reason = if ($finished) { "" } else { "Command timed out after $TimeoutSeconds seconds." }
        $mutated = [bool]($allowed.mutatesByDefault -and -not $DryRun -and -not $PlanOnly)

        $result = New-Result -Ok ($finished -and $exitCode -eq 0) -State $state -Reason $reason -ExitCode $exitCode -Command "powershell" -Args $effectiveArgs -Stdout $stdout -Stderr $stderr -MutatedState $mutated -AllowedScript $allowed
    }
    finally {
        Remove-Item -LiteralPath $temp, $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
    }
}
catch {
    $result = New-Result -Ok $false -State "blocked" -Reason $_.Exception.Message -ExitCode -1 -Command "powershell" -Args @($helperArguments) -Stdout "" -Stderr "" -MutatedState $false -AllowedScript $null
}
finally {
    if ($null -eq $result) {
        $result = New-Result -Ok $false -State "failed" -Reason "Runner ended without producing a result." -ExitCode -1
    }
    $auditPath = Write-AuditEvent -Payload ([pscustomobject]$result)
    $result.auditPath = Get-RelativePath -Path $auditPath
}

[pscustomobject]$result | ConvertTo-Json -Depth 20
