[CmdletBinding()]
param(
    [int]$Port = 8787,
    [string]$Root = "",
    [string]$BearerToken = $env:ORCH_MCP_TOKEN,
    [switch]$NoAuth
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function New-Token {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) }
    finally { $rng.Dispose() }
    return [Convert]::ToBase64String($bytes).TrimEnd("=")
}

if (!$NoAuth -and [string]::IsNullOrWhiteSpace($BearerToken)) {
    $BearerToken = New-Token
    Write-Warning "ORCH_MCP_TOKEN was not set. Generated a temporary token for this process only."
}

$StatusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
$CapabilityStatusScript = Join-Path $Root "scripts\Get-OrchMcpCapabilityStatus.ps1"
$RepoSyncScript = Join-Path $Root "scripts\Invoke-OrchestratorRepoSync.ps1"
$TaskActionScript = Join-Path $Root "scripts\Invoke-OrchestratorTaskAction.ps1"
$AgentActionScript = Join-Path $Root "scripts\Invoke-OrchestratorAgentAction.ps1"
$GitHubCacheScript = Join-Path $Root "scripts\Get-GitHubDataCache.ps1"
$GitHubIssueCommentScript = Join-Path $Root "scripts\Update-GitHubIssueComment.ps1"
$PowerShellPatchScript = Join-Path $Root "scripts\Invoke-OrchestratorPowerShellPatch.ps1"
$SafePowerShellRunnerScript = Join-Path $Root "scripts\Invoke-OrchestratorSafePowerShell.ps1"
$SafePowerShellRunnerFixScript = Join-Path $Root "scripts\Start-OrchMcpServer.SafePowerShellRunnerFix.ps1"
$TunnelCanaryScript = Join-Path $Root "scripts\Test-OrchTunnelCanary.ps1"
$ActiveFleetPlanScript = Join-Path $Root "scripts\Start-ActiveAgentFleet.ps1"
$GitWorkflowScript = Join-Path $Root "scripts\Invoke-OrchestratorGitWorkflow.ps1"
$GitWorkflowToolsScript = Join-Path $Root "scripts\Start-OrchMcpServer.GitWorkflowTools.ps1"
$McpRestartScript = Join-Path $Root "scripts\Restart-OrchMcpServer.ps1"
$ServiceSupervisorScript = Join-Path $Root "scripts\Start-OrchestratorServices.ps1"
$QueueTaskCreateScript = Join-Path $Root "scripts\New-OrchestratorQueueTask.ps1"
$GameMakerProjectInfoScript = Join-Path $Root "scripts\Get-GameMakerProjectInfo.ps1"
$GameMakerCompilerErrorsScript = Join-Path $Root "scripts\Get-GameMakerCompilerErrors.ps1"
$GameMakerSpriteStatusScript = Join-Path $Root "scripts\Get-GameMakerSpriteAssetStatus.ps1"
$GameMakerRoomStatusScript = Join-Path $Root "scripts\Get-GameMakerRoomEditorStatus.ps1"
$GameMakerBuildStatusScript = Join-Path $Root "scripts\Get-GameMakerBuildStatus.ps1"

foreach ($requiredScript in @($StatusScript, $CapabilityStatusScript, $RepoSyncScript, $TaskActionScript, $AgentActionScript, $GitHubCacheScript, $GitHubIssueCommentScript, $PowerShellPatchScript, $SafePowerShellRunnerScript, $SafePowerShellRunnerFixScript, $TunnelCanaryScript, $ActiveFleetPlanScript, $GitWorkflowScript, $GitWorkflowToolsScript, $McpRestartScript, $ServiceSupervisorScript, $GameMakerProjectInfoScript, $GameMakerCompilerErrorsScript, $GameMakerSpriteStatusScript, $GameMakerRoomStatusScript, $GameMakerBuildStatusScript, $QueueTaskCreateScript)) {
    if (!(Test-Path $requiredScript)) { throw "Missing required script: $requiredScript" }
}

function Write-JsonResponse {
    param([System.Net.HttpListenerContext]$Context, [object]$Body, [int]$StatusCode = 200)
    $json = $Body | ConvertTo-Json -Depth 80 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "application/json; charset=utf-8"
    $Context.Response.ContentLength64 = $bytes.Length
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Close()
}

function Write-SseResponse {
    param([System.Net.HttpListenerContext]$Context, [object]$Body, [string]$Event = "message", [int]$StatusCode = 200)
    $json = $Body | ConvertTo-Json -Depth 80 -Compress
    $payload = "event: $Event`ndata: $json`n`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "text/event-stream; charset=utf-8"
    $Context.Response.Headers["Cache-Control"] = "no-cache"
    $Context.Response.Headers["Connection"] = "keep-alive"
    $Context.Response.SendChunked = $true
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Flush()
    $Context.Response.OutputStream.Close()
}

function Write-TextResponse {
    param([System.Net.HttpListenerContext]$Context, [string]$Body, [int]$StatusCode = 200)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "text/plain; charset=utf-8"
    $Context.Response.ContentLength64 = $bytes.Length
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Close()
}

function New-JsonRpcResult {
    param([object]$Id, [object]$Result)
    return [pscustomobject]@{ jsonrpc = "2.0"; id = $Id; result = $Result }
}

function New-JsonRpcError {
    param([object]$Id, [int]$Code, [string]$Message)
    return [pscustomobject]@{ jsonrpc = "2.0"; id = $Id; error = [pscustomobject]@{ code = $Code; message = $Message } }
}

function New-McpInitializeResult {
    return [pscustomobject]@{
        protocolVersion = "2025-03-26"
        capabilities = [pscustomobject]@{ tools = [pscustomobject]@{} }
        serverInfo = [pscustomobject]@{ name = "gm-agent-orchestrator"; version = "0.2.0" }
    }
}

function Test-Authorized {
    param([System.Net.HttpListenerRequest]$Request)
    if ($NoAuth) { return $true }
    $auth = [string]$Request.Headers["Authorization"]
    if ([string]::IsNullOrWhiteSpace($auth)) { return $false }
    if (!$auth.StartsWith("Bearer ")) { return $false }
    $token = $auth.Substring(7).Trim()
    return [string]::Equals($token, $BearerToken, [System.StringComparison]::Ordinal)
}

function Read-RequestJson {
    param([System.Net.HttpListenerRequest]$Request)
    $reader = New-Object System.IO.StreamReader($Request.InputStream, $Request.ContentEncoding)
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    $parsed = $raw | ConvertFrom-Json
    return Normalize-GptJsonRpcRequest -Request $parsed
}

function Normalize-GptJsonRpcRequest {
    param([object]$Request)
    if ($null -eq $Request) { return $null }

    $normalized = [pscustomobject]@{}

    if ($Request.PSObject.Properties["jsonrpc"]) { $normalized | Add-Member -NotePropertyName "jsonrpc" -NotePropertyValue $Request.jsonrpc }
    elseif ([string]::IsNullOrWhiteSpace([string]$Request.jsonrpc)) { $normalized | Add-Member -NotePropertyName "jsonrpc" -NotePropertyValue "2.0" }

    if ($Request.PSObject.Properties["id"]) { $normalized | Add-Member -NotePropertyName "id" -NotePropertyValue $Request.id }
    if ($Request.PSObject.Properties["method"]) { $normalized | Add-Member -NotePropertyName "method" -NotePropertyValue $Request.method }

    if ($Request.PSObject.Properties["params"]) { $normalized | Add-Member -NotePropertyName "params" -NotePropertyValue $Request.params }
    elseif ($Request.PSObject.Properties["arguments"]) { $normalized | Add-Member -NotePropertyName "params" -NotePropertyValue $Request.arguments }
    elseif ($Request.PSObject.Properties["input"]) { $normalized | Add-Member -NotePropertyName "params" -NotePropertyValue $Request.input }

    return $normalized
}

function Invoke-JsonScript {
    param([string]$ScriptPath, [string[]]$Arguments)
    $runId = [Guid]::NewGuid().ToString("N")
    $stdoutPath = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-mcp-{0}.out" -f $runId)
    $stderrPath = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-mcp-{0}.err" -f $runId)
    $argumentList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath) + @($Arguments)
    try {
        $process = Start-Process -FilePath "powershell" -ArgumentList $argumentList -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
        $exitCode = [int]$process.ExitCode
        $stdout = $(if (Test-Path -LiteralPath $stdoutPath -PathType Leaf) { Get-Content -LiteralPath $stdoutPath -Raw } else { "" })
        $stderr = $(if (Test-Path -LiteralPath $stderrPath -PathType Leaf) { Get-Content -LiteralPath $stderrPath -Raw } else { "" })
        $text = ([string]$stdout).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { $text = ([string]$stderr).Trim() }
    }
    finally {
        Remove-Item -LiteralPath $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
    }
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Script emitted no JSON: $ScriptPath" }
    # Strip any prefix lines before the first '{' or '[' — guards against debug/warning
    # lines emitted to stdout by subscripts before the JSON payload (e.g. git warnings
    # captured via 2>&1 that land ahead of the JSON in the output stream).
    $jsonStart = $text.IndexOfAny([char[]]@('{','['))
    if ($jsonStart -gt 0) { $text = $text.Substring($jsonStart) }
    # Sanitize non-ASCII characters that slip through when subscripts read files
    # without -Encoding UTF8 (Windows-1252 default misreads UTF-8 multibyte sequences).
    # Replace any character outside the printable ASCII + safe whitespace range with '?'
    # so ConvertFrom-Json never sees garbled byte sequences inside string values.
    # Also strip bare \r (carriage-return not followed by \n) which can embed in values
    # from Windows line endings and break cross-platform string comparisons.
    $text = [System.Text.RegularExpressions.Regex]::Replace($text, '[^\x09\x0A\x0D\x20-\x7E]', '?')
    try { $json = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Script emitted invalid JSON: $ScriptPath. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0 -and $null -eq $json.PSObject.Properties["ok"]) { throw "Script failed with exit code $($exitCode): $ScriptPath. Error: $stderr" }
    return $json
}

function Test-OptionalSwitchTrue {
    param([object]$Value)
    if ($null -eq $Value) { return $false }
    if ($Value -is [bool]) { return [bool]$Value }

    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return $false }
    return [string]::Equals($text.Trim(), "true", [System.StringComparison]::OrdinalIgnoreCase)
}

$ToolsScript = Join-Path $Root "scripts\Start-OrchMcpServer.Tools.ps1"
if (!(Test-Path $ToolsScript)) { throw "Missing required script: $ToolsScript" }
. $ToolsScript
Copy-Item Function:\Get-ToolsList Function:\Get-ToolsListBase -Force
. $SafePowerShellRunnerFixScript

function Invoke-AgentActionTool {
    param([string]$Action, [object]$Arguments)

    $slot = Get-OptionalJsonProperty -Object $Arguments -Name "slot"
    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$slot)) { throw "Missing required argument: slot" }

    $args = @("-Root", $Root, "-Action", $Action, "-SlotName", [string]$slot)
    $taskPath = Get-OptionalJsonProperty -Object $Arguments -Name "task_path"
    $taskName = Get-OptionalJsonProperty -Object $Arguments -Name "task_name"
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"
    if (-not [string]::IsNullOrWhiteSpace([string]$taskPath) -and -not [string]::IsNullOrWhiteSpace([string]$taskName)) { throw "Specify only one exact task selector: task_path or task_name." }
    if (-not [string]::IsNullOrWhiteSpace([string]$taskPath)) { $args += @("-TaskPath", [string]$taskPath) }
    if (-not [string]::IsNullOrWhiteSpace([string]$taskName)) { $args += @("-TaskName", [string]$taskName) }
    if (Test-OptionalSwitchTrue -Value $dryRun) { $args += "-DryRun" }
    return Invoke-JsonScript -ScriptPath $AgentActionScript -Arguments $args
}

function Get-ToolsList {
    $toolsList = Get-ToolsListBase
    $agentProperties = [pscustomobject]@{ slot = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; task_path = [pscustomobject]@{ type = "string" }; task_name = [pscustomobject]@{ type = "string" } }
    $agentSchema = New-ObjectSchema -Properties $agentProperties -Required @("slot")
    foreach ($tool in @($toolsList.tools)) {
        if ($tool.name -eq "start_agent" -or $tool.name -eq "rerun_agent") { $tool.inputSchema = $agentSchema }
    }
    return $toolsList
}

. $GitWorkflowToolsScript

function Handle-McpJsonRpcRequest {
    param([object]$Request)
    if ($null -eq $Request) { return New-JsonRpcError -Id $null -Code -32700 -Message "Empty or invalid JSON request" }
    $id = Get-JsonRpcProperty -Object $Request -Name "id"
    $method = [string](Get-JsonRpcProperty -Object $Request -Name "method")
    $params = Get-JsonRpcProperty -Object $Request -Name "params"

    switch ($method) {
        "initialize" { return New-JsonRpcResult -Id $id -Result (New-McpInitializeResult) }
        "notifications/initialized" { return [pscustomobject]@{ jsonrpc = "2.0"; result = $null } }
        "tools/list" { return New-JsonRpcResult -Id $id -Result (Get-ToolsList) }
        "tools/call" {
            if ($null -eq $params) { return New-JsonRpcError -Id $id -Code -32602 -Message "Missing params object" }
            $toolName = [string](Get-JsonRpcProperty -Object $params -Name "name")
            if ([string]::IsNullOrWhiteSpace($toolName)) { $toolName = [string](Get-JsonRpcProperty -Object $params -Name "tool") }
            if ([string]::IsNullOrWhiteSpace($toolName)) { return New-JsonRpcError -Id $id -Code -32602 -Message "Missing tool name in params" }
            try {
                $toolArgs = Get-JsonRpcProperty -Object $params -Name "arguments"
                return New-JsonRpcResult -Id $id -Result (Invoke-ToolCall -Name $toolName -Arguments $toolArgs)
            }
            catch { return New-JsonRpcError -Id $id -Code -32000 -Message $_.Exception.Message }
        }
        default { return New-JsonRpcError -Id $id -Code -32601 -Message "Method not found: $method" }
    }
}

$listener = New-Object System.Net.HttpListener
$prefix = "http://127.0.0.1:$Port/"
$listener.Prefixes.Add($prefix)
$listener.Start()
Write-Host "Orch MCP server listening on $prefix"
Write-Host "Endpoint path: /mcp"
Write-Host "SSE endpoint path: /mcp/sse"
if ($NoAuth) { Write-Warning "NoAuth is enabled. Only use with a temporary local/tunnel endpoint." } else { Write-Host "Bearer token auth enabled. Token value is not printed." }
Write-Host "Press Ctrl+C to stop."

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $path = ""
        $stage = "route"
        try {
            $path = $context.Request.Url.AbsolutePath.TrimEnd("/")
            if ($context.Request.HttpMethod -eq "GET" -and $path -eq "/health") { Write-JsonResponse -Context $context -Body ([pscustomobject]@{ ok = $true; service = "gm-agent-orchestrator-mcp"; root = $Root; noAuth = [bool]$NoAuth }); continue }
            if ($path -ne "/mcp" -and $path -ne "/mcp/sse") { Write-TextResponse -Context $context -Body "Not found" -StatusCode 404; continue }
            if (!(Test-Authorized -Request $context.Request)) { Write-JsonResponse -Context $context -Body ([pscustomobject]@{ error = "unauthorized" }) -StatusCode 401; continue }
            if ($context.Request.HttpMethod -eq "GET" -and $path -eq "/mcp/sse") { Write-SseResponse -Context $context -Body (New-JsonRpcResult -Id $null -Result ([pscustomobject]@{ endpoint = "/mcp"; transport = "sse"; serverInfo = (New-McpInitializeResult).serverInfo })) -Event "endpoint"; continue }
            if ($context.Request.HttpMethod -eq "GET") { Write-TextResponse -Context $context -Body "gm-agent-orchestrator MCP endpoint is online. Use JSON-RPC POST requests or GET /mcp/sse for SSE discovery."; continue }
            if ($context.Request.HttpMethod -ne "POST") { Write-TextResponse -Context $context -Body "Method not allowed" -StatusCode 405; continue }
            $stage = "parse"
            $request = Read-RequestJson -Request $context.Request
            $stage = "dispatch"
            $response = Handle-McpJsonRpcRequest -Request $request
            $stage = "response"
            if ($path -eq "/mcp/sse" -or ([string]$context.Request.Headers["Accept"]) -match "text/event-stream") { Write-SseResponse -Context $context -Body $response }
            else { Write-JsonResponse -Context $context -Body $response }
        }
        catch { try { Write-JsonResponse -Context $context -Body ([pscustomobject]@{ error = "mcp_server_error"; message = $_.Exception.Message; path = $path; method = [string]$context.Request.HttpMethod; stage = $stage }) -StatusCode 500 } catch {} }
    }
}
finally {
    if ($listener.IsListening) { $listener.Stop() }
    $listener.Close()
}


