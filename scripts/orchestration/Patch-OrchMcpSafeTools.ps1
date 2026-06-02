<#
.SYNOPSIS
Patch the orchestrator MCP server files to expose the audited safe MCP write tools.

.DESCRIPTION
Idempotently wires the already-audited helpers as first-class MCP tools without
requiring a whole-file rewrite of the MCP server entrypoint or tools script:

- run_safe_powershell -> scripts/Invoke-OrchestratorSafePowerShell.ps1
- create_queue_task -> scripts/New-OrchestratorQueueTask.ps1

The patcher updates required-script checks in the entrypoint and tool-list
schemas, wrapper functions, and Invoke-ToolCall dispatch in the tools script.
It parser-checks patched content for both normal and -DryRun execution.
#>

[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Root = (Resolve-Path (Join-Path $scriptDir "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$serverPath = Join-Path $Root "scripts\Start-OrchMcpServer.ps1"
if (-not (Test-Path -LiteralPath $serverPath -PathType Leaf)) {
    throw "MCP server script was not found: $serverPath"
}

$toolsPath = Join-Path $Root "scripts\Start-OrchMcpServer.Tools.ps1"
if (-not (Test-Path -LiteralPath $toolsPath -PathType Leaf)) {
    throw "MCP server tools script was not found: $toolsPath"
}

function Add-AfterLiteral {
    param(
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$Anchor,
        [Parameter(Mandatory)][string]$Insertion,
        [Parameter(Mandatory)][string]$AlreadyPresent
    )

    if ($Content.Contains($AlreadyPresent)) { return $Content }
    $index = $Content.IndexOf($Anchor, [System.StringComparison]::Ordinal)
    if ($index -lt 0) { throw "Patch anchor not found: $Anchor" }
    $insertAt = $index + $Anchor.Length
    return $Content.Substring(0, $insertAt) + $Insertion + $Content.Substring($insertAt)
}

function Add-BeforeLiteral {
    param(
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$Anchor,
        [Parameter(Mandatory)][string]$Insertion,
        [Parameter(Mandatory)][string]$AlreadyPresent
    )

    if ($Content.Contains($AlreadyPresent)) { return $Content }
    $index = $Content.IndexOf($Anchor, [System.StringComparison]::Ordinal)
    if ($index -lt 0) { throw "Patch anchor not found: $Anchor" }
    return $Content.Substring(0, $index) + $Insertion + $Content.Substring($index)
}

function Replace-RequiredScriptList {
    param([Parameter(Mandatory)][string]$Content)

    $pattern = 'foreach \(\$requiredScript in @\((?<items>[^\)]*)\)\) \{'
    $match = [regex]::Match($Content, $pattern)
    if (-not $match.Success) { throw "Could not find required-script foreach list." }

    $items = $match.Groups['items'].Value
    foreach ($item in @('$PowerShellPatchScript', '$SafePowerShellRunnerScript', '$QueueTaskCreateScript')) {
        if ($items -notmatch [regex]::Escape($item)) {
            $items = $items.TrimEnd() + ", $item"
        }
    }

    return $Content.Substring(0, $match.Groups['items'].Index) + $items + $Content.Substring($match.Groups['items'].Index + $match.Groups['items'].Length)
}

function Assert-ParserClean {
    param([Parameter(Mandatory)][string]$Content)

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseInput($Content, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        $message = ($errors | ForEach-Object { $_.Message }) -join "`n"
        throw "Patched MCP server has parser errors:`n$message"
    }
}

$originalServer = Get-Content -LiteralPath $serverPath -Raw
$serverContent = $originalServer
$originalTools = Get-Content -LiteralPath $toolsPath -Raw
$content = $originalTools

$scriptVariables = @'

$SafePowerShellRunnerScript = Join-Path $Root "scripts\Invoke-OrchestratorSafePowerShell.ps1"
$QueueTaskCreateScript = Join-Path $Root "scripts\New-OrchestratorQueueTask.ps1"
'@

$serverContent = Add-AfterLiteral `
    -Content $serverContent `
    -Anchor '$PowerShellPatchScript = Join-Path $Root "scripts\Invoke-OrchestratorPowerShellPatch.ps1"' `
    -Insertion $scriptVariables.TrimEnd() `
    -AlreadyPresent '$SafePowerShellRunnerScript'

if (-not $serverContent.Contains('$QueueTaskCreateScript')) {
    $queueVariable = @'

$QueueTaskCreateScript = Join-Path $Root "scripts\New-OrchestratorQueueTask.ps1"
'@
    $serverContent = Add-AfterLiteral `
        -Content $serverContent `
        -Anchor '$SafePowerShellRunnerScript = Join-Path $Root "scripts\Invoke-OrchestratorSafePowerShell.ps1"' `
        -Insertion $queueVariable.TrimEnd() `
        -AlreadyPresent '$QueueTaskCreateScript'
}

$serverContent = Replace-RequiredScriptList -Content $serverContent

$safeRunnerWrapper = @'

function Invoke-SafePowerShellRunnerTool {
    param([object]$Arguments)

    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.script_name)) { throw "Missing required argument: script_name" }
    $scriptName = [string]$Arguments.script_name
    $args = @("-Root", $Root, "-ScriptName", $scriptName)

    $argumentJson = Get-OptionalJsonProperty -Object $Arguments -Name "argument_json"
    $argumentJsonBase64 = Get-OptionalJsonProperty -Object $Arguments -Name "argument_json_base64"
    $rawArguments = Get-OptionalJsonProperty -Object $Arguments -Name "arguments"
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"
    $planOnly = Get-OptionalJsonProperty -Object $Arguments -Name "plan_only"
    $timeoutSeconds = Get-OptionalJsonProperty -Object $Arguments -Name "timeout_seconds"

    if (-not [string]::IsNullOrWhiteSpace([string]$argumentJson)) { $args += @("-ArgumentJson", [string]$argumentJson) }
    elseif (-not [string]::IsNullOrWhiteSpace([string]$argumentJsonBase64)) { $args += @("-ArgumentJsonBase64", [string]$argumentJsonBase64) }
    elseif ($null -ne $rawArguments) { $args += @("-ArgumentJson", ($rawArguments | ConvertTo-Json -Depth 80 -Compress)) }
    if ($true -eq [bool]$dryRun) { $args += "-DryRun" }
    if ($true -eq [bool]$planOnly) { $args += "-PlanOnly" }
    if ($null -ne $timeoutSeconds) { $args += @("-TimeoutSeconds", [string]$timeoutSeconds) }

    return Invoke-JsonScript -ScriptPath $SafePowerShellRunnerScript -Arguments $args
}
'@

$queueWrapper = @'

function Invoke-CreateQueueTaskTool {
    param([object]$Arguments)

    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.title)) { throw "Missing required argument: title" }
    $args = @("-Root", $Root, "-Title", [string]$Arguments.title)

    $body = Get-OptionalJsonProperty -Object $Arguments -Name "body"
    $reason = Get-OptionalJsonProperty -Object $Arguments -Name "reason"
    $priority = Get-OptionalJsonProperty -Object $Arguments -Name "priority"
    $owner = Get-OptionalJsonProperty -Object $Arguments -Name "owner"
    $blockedBy = Get-OptionalJsonProperty -Object $Arguments -Name "blocked_by"
    if ($null -eq $blockedBy) { $blockedBy = Get-OptionalJsonProperty -Object $Arguments -Name "blockedBy" }
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"

    if (-not [string]::IsNullOrWhiteSpace([string]$body)) { $args += @("-Body", [string]$body) }
    if (-not [string]::IsNullOrWhiteSpace([string]$reason)) { $args += @("-Reason", [string]$reason) }
    if (-not [string]::IsNullOrWhiteSpace([string]$priority)) { $args += @("-Priority", [string]$priority) }
    if (-not [string]::IsNullOrWhiteSpace([string]$owner)) { $args += @("-Owner", [string]$owner) }
    if (-not [string]::IsNullOrWhiteSpace([string]$blockedBy)) { $args += @("-BlockedBy", [string]$blockedBy) }
    if ($null -eq $dryRun -or $true -eq $dryRun -or "true" -eq [string]$dryRun) { $args += "-DryRun" }

    return Invoke-JsonScript -ScriptPath $QueueTaskCreateScript -Arguments $args
}
'@

$content = Add-BeforeLiteral `
    -Content $content `
    -Anchor 'function New-ToolTextResult {' `
    -Insertion $safeRunnerWrapper `
    -AlreadyPresent 'function Invoke-SafePowerShellRunnerTool'

$content = Add-BeforeLiteral `
    -Content $content `
    -Anchor 'function New-ToolTextResult {' `
    -Insertion $queueWrapper `
    -AlreadyPresent 'function Invoke-CreateQueueTaskTool'

$toolSchemaInsertion = @'
            [pscustomobject]@{ name = "run_safe_powershell"; description = "Run an allowlisted orchestrator PowerShell helper through the audited safe runner."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ script_name = [pscustomobject]@{ type = "string" }; argument_json = [pscustomobject]@{ type = "string" }; argument_json_base64 = [pscustomobject]@{ type = "string" }; arguments = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" } }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; plan_only = [pscustomobject]@{ type = "boolean"; default = $false }; timeout_seconds = [pscustomobject]@{ type = "integer"; minimum = 1; maximum = 600; default = 120 } }) -Required @("script_name") },
            [pscustomobject]@{ name = "create_queue_task"; description = "Create an orchestrator queue task through the audited queue helper. Use dry_run=true to preview."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ title = [pscustomobject]@{ type = "string" }; body = [pscustomobject]@{ type = "string" }; reason = [pscustomobject]@{ type = "string" }; priority = [pscustomobject]@{ type = "string"; enum = @("P0", "P1", "P2"); default = "P1" }; owner = [pscustomobject]@{ type = "string"; enum = @("claude", "codex", "gemini", "gpt", "human", "operator-intake"); default = "claude" }; blocked_by = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $true } }) -Required @("title") },
'@

$toolSchemaInsertion = $toolSchemaInsertion.Replace('\"', '"')

if (-not $content.Contains('name = "run_safe_powershell"')) {
    $content = Add-AfterLiteral `
        -Content $content `
        -Anchor '            [pscustomobject]@{ name = "promote_powershell_patch"; description = "Promote a staged PowerShell patch with backup support. Defaults to dry_run=true."; inputSchema = New-ObjectSchema -Properties $patchProperties -Required @("patch_id") },' `
        -Insertion ("`r`n" + $toolSchemaInsertion.TrimEnd()) `
        -AlreadyPresent 'name = "run_safe_powershell"'
}
elseif (-not $content.Contains('name = "create_queue_task"')) {
    $queueSchema = ($toolSchemaInsertion -split "`r?`n" | Where-Object { $_ -match 'name = "create_queue_task"' }) -join "`r`n"
    $content = Add-BeforeLiteral `
        -Content $content `
        -Anchor '            [pscustomobject]@{ name = "get_gamemaker_project_info"' `
        -Insertion ($queueSchema + "`r`n") `
        -AlreadyPresent 'name = "create_queue_task"'
}

$dispatchInsertion = @'
        "run_safe_powershell" { return New-ToolTextResult -Value (Invoke-SafePowerShellRunnerTool -Arguments $Arguments) }
        "create_queue_task" { return New-ToolTextResult -Value (Invoke-CreateQueueTaskTool -Arguments $Arguments) }
'@
$dispatchInsertion = $dispatchInsertion.Replace('\"', '"')

if (-not $content.Contains('"run_safe_powershell" {')) {
    $content = Add-AfterLiteral `
        -Content $content `
        -Anchor '        "promote_powershell_patch" { return New-ToolTextResult -Value (Invoke-PowerShellPatchTool -Action "promote" -Arguments $Arguments) }' `
        -Insertion ("`r`n" + $dispatchInsertion.TrimEnd()) `
        -AlreadyPresent '"run_safe_powershell" {'
}
elseif (-not $content.Contains('"create_queue_task" {')) {
    $createQueueTaskDispatch = "        ""create_queue_task"" { return New-ToolTextResult -Value (Invoke-CreateQueueTaskTool -Arguments `$Arguments) }`r`n"
    $content = Add-BeforeLiteral `
        -Content $content `
        -Anchor '        "get_gamemaker_project_info" { return New-ToolTextResult -Value (Get-GameMakerProjectInfoTool -Arguments $Arguments) }' `
        -Insertion $createQueueTaskDispatch `
        -AlreadyPresent '"create_queue_task" {'
}

$serverChanged = -not [string]::Equals($originalServer, $serverContent, [System.StringComparison]::Ordinal)
$toolsChanged = -not [string]::Equals($originalTools, $content, [System.StringComparison]::Ordinal)
$changed = $serverChanged -or $toolsChanged
Assert-ParserClean -Content $serverContent
Assert-ParserClean -Content $content

if ($changed -and -not $DryRun) {
    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
    if ($serverChanged) {
        Copy-Item -LiteralPath $serverPath -Destination "$serverPath.$timestamp.bak" -Force
        Set-Content -LiteralPath $serverPath -Value $serverContent -Encoding UTF8
    }
    if ($toolsChanged) {
        Copy-Item -LiteralPath $toolsPath -Destination "$toolsPath.$timestamp.bak" -Force
        Set-Content -LiteralPath $toolsPath -Value $content -Encoding UTF8
    }
}

[pscustomobject]@{
    ok = $true
    action = "patch_orch_mcp_safe_tools"
    changed = $changed
    dryRun = [bool]$DryRun
    paths = @($serverPath, $toolsPath)
    wiredTools = @("run_safe_powershell", "create_queue_task")
} | ConvertTo-Json -Depth 10
