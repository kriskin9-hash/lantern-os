[CmdletBinding()]
param(
    [string]$Root = "",
    [int]$CurrentPort = 8787,
    [int]$CandidatePort = 8788,
    [switch]$NoAuth,
    [switch]$DryRun,
    [switch]$FullPayload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$ServerScript = Join-Path $Root "scripts\Start-OrchMcpServer.ps1"
if (!(Test-Path -LiteralPath $ServerScript -PathType Leaf)) { throw "Missing MCP server script: $ServerScript" }

function Invoke-McpTool {
    param([int]$Port, [string]$ToolName, [object]$Arguments = $null)

    $params = @{ name = $ToolName; arguments = $(if ($null -ne $Arguments) { $Arguments } else { [pscustomobject]@{} }) }
    $body = @{ jsonrpc = "2.0"; id = 1; method = "tools/call"; params = $params } | ConvertTo-Json -Depth 40
    return Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 15
}

function ConvertFrom-McpToolSummary {
    param([string]$ToolName, [object]$Response)

    $summary = [ordered]@{
        tool = $ToolName
        jsonrpcOk = $false
        ok = $null
        count = $null
        error = ""
        firstNumber = $null
        firstTitle = $null
    }

    if ($null -eq $Response) {
        $summary.error = "empty_response"
        return [pscustomobject]$summary
    }

    if ($null -ne $Response.PSObject.Properties["error"]) {
        $summary.error = [string]$Response.error.message
        return [pscustomobject]$summary
    }

    $summary.jsonrpcOk = $true

    if ($null -eq $Response.PSObject.Properties["result"] -or $null -eq $Response.result.PSObject.Properties["content"] -or @($Response.result.content).Count -lt 1) {
        $summary.error = "missing_result_content"
        return [pscustomobject]$summary
    }

    $text = [string]$Response.result.content[0].text
    if ([string]::IsNullOrWhiteSpace($text)) {
        $summary.error = "empty_text_payload"
        return [pscustomobject]$summary
    }

    try {
        $inner = $text | ConvertFrom-Json -ErrorAction Stop
        if ($null -ne $inner.PSObject.Properties["ok"]) { $summary.ok = [bool]$inner.ok }
        if ($null -ne $inner.PSObject.Properties["count"]) { $summary.count = [int]$inner.count }
        if ($null -ne $inner.PSObject.Properties["error"]) { $summary.error = [string]$inner.error }
        if ($null -ne $inner.PSObject.Properties["issues"] -and @($inner.issues).Count -gt 0) {
            $summary.firstNumber = $inner.issues[0].number
            $summary.firstTitle = $inner.issues[0].title
        }
        elseif ($null -ne $inner.PSObject.Properties["prs"] -and @($inner.prs).Count -gt 0) {
            $summary.firstNumber = $inner.prs[0].number
            $summary.firstTitle = $inner.prs[0].title
        }
        elseif ($ToolName -eq "get_mcp_capability_status") {
            if ($null -ne $inner.PSObject.Properties["state"]) { $summary.ok = ([string]$inner.state -in @("ready", "online", "online_writable")) }
            if ($null -ne $inner.PSObject.Properties["mode"]) { $summary.firstTitle = [string]$inner.mode }
        }
    }
    catch {
        $summary.error = "invalid_inner_json: $($_.Exception.Message)"
    }

    return [pscustomobject]$summary
}

function Test-PortHealth {
    param([int]$Port)
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -Method Get -TimeoutSec 5
        return [bool]$health.ok
    }
    catch { return $false }
}

function New-Result {
    param([bool]$Ok, [string]$State, [string]$ErrorMessage = "", [object]$Extra = $null)
    $payload = [ordered]@{
        ok = $Ok
        state = $State
        dryRun = [bool]$DryRun
        fullPayload = [bool]$FullPayload
        root = $Root
        currentPort = $CurrentPort
        candidatePort = $CandidatePort
        error = $ErrorMessage
        generatedAt = (Get-Date).ToString("o")
    }
    if ($null -ne $Extra) {
        foreach ($property in $Extra.PSObject.Properties) { $payload[$property.Name] = $property.Value }
    }
    [Console]::Out.WriteLine(([pscustomobject]$payload | ConvertTo-Json -Depth 80 -Compress))
}

try {
    $currentBefore = [pscustomobject]@{
        health = Test-PortHealth -Port $CurrentPort
        checks = [ordered]@{}
    }
    $currentBeforeFull = [ordered]@{}

    foreach ($tool in @("get_github_issues_cached", "get_github_pr_status_cached", "get_mcp_capability_status")) {
        try {
            $toolResult = Invoke-McpTool -Port $CurrentPort -ToolName $tool
            $currentBefore.checks[$tool] = ConvertFrom-McpToolSummary -ToolName $tool -Response $toolResult
            if ($FullPayload) { $currentBeforeFull[$tool] = $toolResult }
        }
        catch {
            New-Result -Ok $false -State "blocked_current_mcp_unhealthy" -ErrorMessage "Current MCP failed ${tool}: $($_.Exception.Message)" -Extra ([pscustomobject]@{ currentBefore = $currentBefore })
            exit 0
        }
    }

    if ($DryRun) {
        $extra = [ordered]@{ currentBefore = $currentBefore; candidateStarted = $false }
        if ($FullPayload) { $extra.currentBeforeFull = [pscustomobject]$currentBeforeFull }
        New-Result -Ok $true -State "dry_run_current_validated" -Extra ([pscustomobject]$extra)
        exit 0
    }

    if (Test-PortHealth -Port $CandidatePort) {
        New-Result -Ok $false -State "blocked_candidate_port_in_use" -ErrorMessage "Candidate port $CandidatePort is already serving health."
        exit 0
    }

    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ServerScript, "-Root", $Root, "-Port", [string]$CandidatePort)
    if ($NoAuth) { $args += "-NoAuth" }

    $candidate = Start-Process powershell -ArgumentList $args -WorkingDirectory $Root -PassThru
    Start-Sleep -Seconds 5

    $candidateHealth = Test-PortHealth -Port $CandidatePort
    if (!$candidateHealth) {
        try { Stop-Process -Id $candidate.Id -Force -ErrorAction SilentlyContinue } catch {}
        New-Result -Ok $false -State "blocked_candidate_unhealthy" -ErrorMessage "Candidate MCP did not pass /health." -Extra ([pscustomobject]@{ candidatePid = $candidate.Id })
        exit 0
    }

    $candidateChecks = [ordered]@{}
    $candidateChecksFull = [ordered]@{}
    foreach ($tool in @("get_github_issues_cached", "get_github_pr_status_cached", "get_mcp_capability_status")) {
        try {
            $toolResult = Invoke-McpTool -Port $CandidatePort -ToolName $tool
            $candidateChecks[$tool] = ConvertFrom-McpToolSummary -ToolName $tool -Response $toolResult
            if ($FullPayload) { $candidateChecksFull[$tool] = $toolResult }
        }
        catch {
            try { Stop-Process -Id $candidate.Id -Force -ErrorAction SilentlyContinue } catch {}
            New-Result -Ok $false -State "blocked_candidate_tool_failed" -ErrorMessage "Candidate MCP failed ${tool}: $($_.Exception.Message)" -Extra ([pscustomobject]@{ candidatePid = $candidate.Id; candidateChecks = [pscustomobject]$candidateChecks })
            exit 0
        }
    }

    $currentAfter = [pscustomobject]@{ health = Test-PortHealth -Port $CurrentPort }
    $extra = [ordered]@{
        currentBefore = $currentBefore
        currentAfter = $currentAfter
        candidatePid = $candidate.Id
        candidateHealth = $candidateHealth
        candidateChecks = [pscustomobject]$candidateChecks
        handoffRequired = "manual_or_supervisor_switch_after_review"
    }
    if ($FullPayload) { $extra.candidateChecksFull = [pscustomobject]$candidateChecksFull }
    New-Result -Ok $true -State "candidate_validated_no_handoff" -Extra ([pscustomobject]$extra)
}
catch {
    New-Result -Ok $false -State "failed_exception" -ErrorMessage $_.Exception.Message
}
