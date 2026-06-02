[CmdletBinding()]
param(
    [int]$Port = 8765,
    [switch]$NoOpen,
    [switch]$NoRefresh
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path

if (-not $NoRefresh) {
    & (Join-Path $PSScriptRoot "Get-OrchestratorStatus.ps1") -Root $root | Out-Null
}

$listener = [System.Net.HttpListener]::new()
$prefix = "http://localhost:$Port/"
$listener.Prefixes.Add($prefix)

try {
    $listener.Start()
}
catch {
    throw "Could not start HttpListener on $prefix. $($_.Exception.Message)"
}

Write-Host "Dashboard server: $prefix"
Write-Host "Serving root: $root"
Write-Host "Stop with Ctrl-C in this window."

if (-not $NoOpen) {
    Start-Process "${prefix}dashboard/index-v2.html"
}

$mime = @{
    ".html" = "text/html; charset=utf-8"
    ".htm"  = "text/html; charset=utf-8"
    ".js"   = "application/javascript; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".md"   = "text/plain; charset=utf-8"
    ".txt"  = "text/plain; charset=utf-8"
    ".log"  = "text/plain; charset=utf-8"
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".svg"  = "image/svg+xml"
    ".ico"  = "image/x-icon"
}

$statusScript = Join-Path $PSScriptRoot "Get-OrchestratorStatus.ps1"
$statusJsonPath = Join-Path $root "status\orchestrator.json"
$statusLock = New-Object Object

function Resolve-DashboardRequestPath {
    param([string]$AbsolutePath)

    $decodedPath = [System.Net.WebUtility]::UrlDecode($AbsolutePath)
    $normalizedPath = $decodedPath.TrimEnd("/")

    if ([string]::IsNullOrWhiteSpace($normalizedPath)) {
        return "dashboard\index-v2.html"
    }

    if ($normalizedPath -eq "/dashboard" -or $normalizedPath -eq "/dashboard/index.html") {
        return "dashboard\index-v2.html"
    }

    $relativePath = $decodedPath.TrimStart("/") -replace "/", "\"
    if ([string]::IsNullOrWhiteSpace($relativePath)) {
        return "dashboard\index-v2.html"
    }

    return $relativePath
}

function Write-BytesResponse {
    param(
        [System.Net.HttpListenerResponse]$Response,
        [byte[]]$Bytes,
        [string]$ContentType,
        [int]$StatusCode = 200
    )

    $Response.StatusCode = $StatusCode
    $Response.ContentType = $ContentType
    $Response.AddHeader("Cache-Control", "no-cache, no-store, must-revalidate")
    $Response.ContentLength64 = $Bytes.Length
    $Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
}

function Write-TextResponse {
    param(
        [System.Net.HttpListenerResponse]$Response,
        [string]$Text,
        [int]$StatusCode = 200,
        [string]$ContentType = "text/plain; charset=utf-8"
    )

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    Write-BytesResponse -Response $Response -Bytes $bytes -ContentType $ContentType -StatusCode $StatusCode
}

function Get-AgentSlotNames {
    $configPath = Join-Path $root "config\agents.json"
    if (-not (Test-Path $configPath)) {
        $configPath = Join-Path $root "config\agents.example.json"
    }

    if (-not (Test-Path $configPath)) { return @() }

    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    return @($config.slots | ForEach-Object { [string]$_.name } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function Set-DashboardSlotLock {
    param(
        [string]$SlotName,
        [bool]$Locked,
        [string]$Owner,
        [string]$Reason
    )

    if ([string]::IsNullOrWhiteSpace($SlotName)) { throw "slot is required" }
    if ($SlotName -match "[\\/\.]") { throw "slot must be a configured slot name, not a path" }

    $validSlots = @(Get-AgentSlotNames)
    if ($validSlots.Count -eq 0) { throw "No configured agent slots were found." }
    if ($validSlots -notcontains $SlotName) {
        throw "Invalid slot '$SlotName'. Expected one of: $($validSlots -join ', ')"
    }

    $locksDir = Join-Path $root "locks"
    New-Item -ItemType Directory -Force -Path $locksDir | Out-Null
    $lockPath = Join-Path $locksDir ("{0}.manual.lock" -f $SlotName)

    if ($Locked) {
        $lock = [pscustomobject]@{
            slot = $SlotName
            owner = $(if ([string]::IsNullOrWhiteSpace($Owner)) { "Alex" } else { $Owner })
            reason = $(if ([string]::IsNullOrWhiteSpace($Reason)) { "dashboard toggle" } else { $Reason })
            createdAt = (Get-Date).ToString("o")
            expiresAt = $null
            machine = $env:COMPUTERNAME
        }
        $lock | ConvertTo-Json -Depth 5 | Set-Content -Path $lockPath -Encoding UTF8
    }
    else {
        if (Test-Path $lockPath) { Remove-Item $lockPath -Force }
    }
}

function New-StatusFallbackJson {
    param([string]$Message)

    $safeMessage = $(if ([string]::IsNullOrWhiteSpace($Message)) { "Unknown dashboard status error." } else { $Message })
    $status = [pscustomobject]@{
        generatedAt = (Get-Date).ToString("o")
        root = $root
        state = "needs_attention"
        headline = "Dashboard status backend is blocked."
        nextAction = [pscustomobject]@{
            action = "Check the dashboard server console for the first status script error; the dashboard is still running."
            owner = "orchestrator"
            when = "now"
            blockedBy = "status API error"
        }
        priorityWarnings = @($safeMessage)
        bridgeValidation = [pscustomobject]@{
            state = "unresolved"
            taskPath = "tasks/queue/p0-validate-chatgpt-bridge-tool-visibility.md"
            logPath = "scripts/Start-Dashboard.ps1"
            blocker = "Status API error"
            nextAction = "Restore /api/status and run bridge validation through manual ChatGPT fallback."
            chatgptFallbackPrompt = @(
                "Manual fallback handler for RC1 bridge validation.",
                "Task path: tasks/queue/p0-validate-chatgpt-bridge-tool-visibility.md",
                "Log path: scripts/Start-Dashboard.ps1",
                "Return one classification: A, B, or C, with brief evidence."
            ) -join "`n"
        }
        watcher = [pscustomobject]@{
            state = "unknown"
            statusText = "Watcher status is unavailable because status generation failed."
        }
        counts = [pscustomobject]@{
            queue = 0
            active = 0
            done = 0
            failed = 0
        }
        tasks = [pscustomobject]@{
            queue = @()
            active = @()
            done = @()
            failed = @()
        }
        slots = @(
            [pscustomobject]@{
                name = "dashboard"
                state = "blocked"
                statusText = "Dashboard server is online, but /api/status could not refresh orchestrator status."
                currentTask = $null
                latestLog = [pscustomobject]@{
                    name = "status-api-error"
                    path = "scripts/Start-Dashboard.ps1"
                    lastWriteTime = (Get-Date).ToString("o")
                    ageMinutes = 0
                    importantLine = $safeMessage
                    tail = $safeMessage
                }
                blocker = [pscustomobject]@{
                    kind = "status_api_error"
                    label = "Status API error"
                    severity = "blocked"
                    nextAction = "Fix the first status script error so /api/status can return live data."
                }
                manualLock = $null
                limit = $null
                nextAction = [pscustomobject]@{
                    action = "Fix the first status script error so /api/status can return live data."
                    owner = "orchestrator"
                    when = "now"
                    blockedBy = "status API error"
                }
            }
        )
    }

    return ($status | ConvertTo-Json -Depth 20)
}

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        try {
            $absPath = $request.Url.AbsolutePath

            if ($absPath -eq "/api/status") {
                [System.Threading.Monitor]::Enter($statusLock)
                try {
                    try {
                        & $statusScript -Root $root | Out-Null
                        $bytes = [System.IO.File]::ReadAllBytes($statusJsonPath)
                        Write-BytesResponse -Response $response -Bytes $bytes -ContentType "application/json; charset=utf-8"
                    }
                    catch {
                        $fallback = New-StatusFallbackJson -Message $_.Exception.Message
                        Write-TextResponse -Response $response -Text $fallback -ContentType "application/json; charset=utf-8"
                    }
                }
                finally {
                    [System.Threading.Monitor]::Exit($statusLock)
                }

                continue
            }

            if ($absPath -eq "/api/crash-cart") {
                if ($request.HttpMethod -ne "POST") {
                    Write-TextResponse -Response $response -Text "POST required" -StatusCode 405
                    continue
                }

                $reader = [System.IO.StreamReader]::new($request.InputStream, $request.ContentEncoding)
                try { $body = $reader.ReadToEnd() }
                finally { $reader.Close() }

                if ([string]::IsNullOrWhiteSpace($body)) {
                    Write-TextResponse -Response $response -Text "Request body is required" -StatusCode 400
                    continue
                }

                try {
                    $payload = $body | ConvertFrom-Json
                    $message = [string]$payload.message
                    if ([string]::IsNullOrWhiteSpace($message)) {
                        Write-TextResponse -Response $response -Text '{"error":"message field required"}' -StatusCode 400 -ContentType "application/json; charset=utf-8"
                        continue
                    }

                    # Forward request to GPT Web API service
                    $gptWebApiUrl = "http://localhost:3000/api/chat"
                    $gptPayload = @{ message = $message } | ConvertTo-Json

                    try {
                        $result = Invoke-WebRequest -Uri $gptWebApiUrl -Method POST -Body $gptPayload -ContentType "application/json" -ErrorAction Stop
                        Write-TextResponse -Response $response -Text $result.Content -ContentType "application/json; charset=utf-8"
                    }
                    catch {
                        $errorJson = [pscustomobject]@{
                            error = "GPT Web API unavailable: $_"
                            hint = "Start the GPT Web API server with: scripts\Start-GptWebApiServer.ps1 -Wait"
                        } | ConvertTo-Json -Compress
                        Write-TextResponse -Response $response -Text $errorJson -StatusCode 503 -ContentType "application/json; charset=utf-8"
                    }
                    continue
                }
                catch {
                    $errorJson = [pscustomobject]@{ error = $_.Exception.Message } | ConvertTo-Json -Compress
                    Write-TextResponse -Response $response -Text $errorJson -StatusCode 500 -ContentType "application/json; charset=utf-8"
                    continue
                }
            }

            if ($absPath -eq "/api/slot-lock") {
                if ($request.HttpMethod -ne "POST") {
                    Write-TextResponse -Response $response -Text "POST required" -StatusCode 405
                    continue
                }

                $reader = [System.IO.StreamReader]::new($request.InputStream, $request.ContentEncoding)
                try { $body = $reader.ReadToEnd() }
                finally { $reader.Close() }

                if ([string]::IsNullOrWhiteSpace($body)) {
                    Write-TextResponse -Response $response -Text "Request body is required" -StatusCode 400
                    continue
                }

                try {
                    $payload = $body | ConvertFrom-Json
                    $slot = [string]$payload.slot
                    $locked = [bool]$payload.locked
                    $owner = $(if ($null -eq $payload.owner) { "Alex" } else { [string]$payload.owner })
                    $reason = $(if ($null -eq $payload.reason) { "dashboard toggle" } else { [string]$payload.reason })

                    [System.Threading.Monitor]::Enter($statusLock)
                    try {
                        Set-DashboardSlotLock -SlotName $slot -Locked $locked -Owner $owner -Reason $reason
                        try {
                            & $statusScript -Root $root | Out-Null
                            $bytes = [System.IO.File]::ReadAllBytes($statusJsonPath)
                            Write-BytesResponse -Response $response -Bytes $bytes -ContentType "application/json; charset=utf-8"
                        }
                        catch {
                            $fallback = New-StatusFallbackJson -Message $_.Exception.Message
                            Write-TextResponse -Response $response -Text $fallback -ContentType "application/json; charset=utf-8"
                        }
                    }
                    finally {
                        [System.Threading.Monitor]::Exit($statusLock)
                    }

                    continue
                }
                catch {
                    Write-TextResponse -Response $response -Text $_.Exception.Message -StatusCode 400
                    continue
                }
            }

            $relPath = Resolve-DashboardRequestPath -AbsolutePath $absPath

            if ($relPath -match "\.\.") {
                $response.StatusCode = 400
                continue
            }

            $candidate = Join-Path $root $relPath
            if ((Test-Path $candidate) -and ((Get-Item $candidate).PSIsContainer)) {
                $candidate = Join-Path $candidate "index.html"
            }

            if (-not (Test-Path $candidate)) {
                Write-TextResponse -Response $response -Text "Not found: $relPath" -StatusCode 404
                continue
            }

            $ext = [System.IO.Path]::GetExtension($candidate).ToLowerInvariant()
            $contentType = $(if ($mime.ContainsKey($ext)) { $mime[$ext] } else { "application/octet-stream" })

            $bytes = [System.IO.File]::ReadAllBytes($candidate)
            Write-BytesResponse -Response $response -Bytes $bytes -ContentType $contentType
        }
        catch {
            try { Write-TextResponse -Response $response -Text "Server error: $($_.Exception.Message)" -StatusCode 500 }
            catch {}
        }
        finally {
            try { $response.OutputStream.Close() } catch {}
        }
    }
}
finally {
    $listener.Stop()
    $listener.Close()
}
