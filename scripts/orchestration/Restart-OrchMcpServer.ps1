[CmdletBinding()]
param(
    [string]$Root = "",
    [ValidateRange(1, 65535)]
    [int]$Port = 8787,
    [ValidateSet("true", "false", "1", "0", "True", "False")]
    [string]$NoAuth = "true",
    [ValidateRange(0, 60)]
    [int]$DelaySeconds = 2,
    [string]$Reason = "",
    [switch]$DryRun,
    [switch]$Worker
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
$NoAuthEnabled = $NoAuth -in @("true", "1", "True")

$serverScript = Join-Path $Root "scripts\Start-OrchMcpServer.ps1"
if (-not (Test-Path -LiteralPath $serverScript -PathType Leaf)) {
    throw "MCP server script not found: $serverScript"
}

function ConvertTo-AuditPath {
    param([string]$Action)
    $dir = Join-Path $Root "logs\control-actions"
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    return Join-Path $dir ("{0}-{1}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $Action)
}

function Write-Audit {
    param([object]$Payload, [string]$Action = "restart_mcp_server")
    $path = ConvertTo-AuditPath -Action $Action
    $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

function Get-RelativePathOrSelf {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd("\", "/")
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    if ($pathFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $pathFull.Substring($rootFull.Length).TrimStart("\", "/") -replace "\\", "/"
    }
    return $pathFull
}

function Get-McpServerProcesses {
    $escapedServer = [regex]::Escape($serverScript)
    $serverNamePattern = '(?i)(^|[\\/\s"''])Start-OrchMcpServer\.ps1($|[\s"''])'
    $portPattern = "(?i)(^|\s)-Port\s+$Port(\s|$)"
    $processes = @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'pwsh.exe'" -ErrorAction SilentlyContinue | Where-Object {
            $commandLine = [string]$_.CommandLine
            if ([string]::IsNullOrWhiteSpace($commandLine)) { return $false }
            $isServer = ($commandLine -match $escapedServer) -or ($commandLine -match $serverNamePattern)
            if (-not $isServer) { return $false }
            if ($commandLine -match "(?i)(^|\s)-Port\s+") { return ($commandLine -match $portPattern) }
            return ($Port -eq 8787)
        } | ForEach-Object {
            [pscustomobject]@{
                processId = [int]$_.ProcessId
                name = [string]$_.Name
                commandLine = [string]$_.CommandLine
            }
        })
    return $processes
}

function New-StartArguments {
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $serverScript, "-Port", [string]$Port, "-Root", $Root)
    if ($NoAuthEnabled) { $args += "-NoAuth" }
    return $args
}

$baseResult = [ordered]@{
    ok = $true
    action = "restart_mcp_server"
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    port = $Port
    noAuth = [bool]$NoAuthEnabled
    dryRun = [bool]$DryRun
    worker = [bool]$Worker
    delaySeconds = $DelaySeconds
    reason = $Reason
    healthUrl = "http://127.0.0.1:$Port/health"
    mcpUrl = "http://127.0.0.1:$Port/mcp"
    targetProcesses = @()
    command = @()
    workerProcessId = $null
    auditPath = ""
    error = ""
}

try {
    $targets = @(Get-McpServerProcesses)
    $baseResult.targetProcesses = @($targets | ForEach-Object {
            [pscustomobject]@{
                processId = $_.processId
                name = $_.name
                commandLine = $_.commandLine
            }
        })
    $baseResult.command = @("powershell") + (New-StartArguments)

    if ($DryRun) {
        $baseResult.auditPath = Get-RelativePathOrSelf -Path (Write-Audit -Payload ([pscustomobject]$baseResult) -Action "restart_mcp_server-dry_run")
        [pscustomobject]$baseResult | ConvertTo-Json -Depth 20
        return
    }

    if ($Worker) {
        Start-Sleep -Seconds $DelaySeconds
        foreach ($target in $targets) {
            Stop-Process -Id $target.processId -Force -ErrorAction Stop
        }
        Start-Process -FilePath "powershell" -ArgumentList (New-StartArguments) -WorkingDirectory $Root -WindowStyle Hidden | Out-Null
        $baseResult.auditPath = Get-RelativePathOrSelf -Path (Write-Audit -Payload ([pscustomobject]$baseResult) -Action "restart_mcp_server-worker")
        [pscustomobject]$baseResult | ConvertTo-Json -Depth 20
        return
    }

    $workerArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "-Root", $Root, "-Port", [string]$Port, "-DelaySeconds", [string]$DelaySeconds, "-Reason", $Reason, "-NoAuth", $NoAuth.ToLowerInvariant(), "-Worker")
    $process = Start-Process -FilePath "powershell" -ArgumentList $workerArgs -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    $baseResult.workerProcessId = $process.Id
    $baseResult.auditPath = Get-RelativePathOrSelf -Path (Write-Audit -Payload ([pscustomobject]$baseResult) -Action "restart_mcp_server-scheduled")
}
catch {
    $baseResult.ok = $false
    $baseResult.error = $_.Exception.Message
    try { $baseResult.auditPath = Get-RelativePathOrSelf -Path (Write-Audit -Payload ([pscustomobject]$baseResult) -Action "restart_mcp_server-error") } catch {}
}

[pscustomobject]$baseResult | ConvertTo-Json -Depth 20
