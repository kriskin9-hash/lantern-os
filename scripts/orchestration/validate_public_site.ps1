param(
    [string]$BaseUrl = "https://human-flourishing-frameworks.onrender.com",
    [int]$Retries = 3,
    [int]$RetryDelaySeconds = 10
)

$ErrorActionPreference = "Stop"

function Invoke-WithRetry {
    param(
        [scriptblock]$Action,
        [string]$Label
    )

    $lastError = $null
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            return & $Action
        }
        catch {
            $lastError = $_
            Write-Warning "${Label} failed on attempt ${i}/${Retries}: $($_.Exception.Message)"
            if ($i -lt $Retries) {
                Start-Sleep -Seconds $RetryDelaySeconds
            }
        }
    }

    throw $lastError
}

$BaseUrl = $BaseUrl.TrimEnd("/")
$ForbiddenPhrases = @(
    "ALGORITHMIC GOVERNANCE",
    "No human board",
    "irreversible after a 24-hour lock"
)
$RequiredPhrases = @(
    "Human Flourishing Frameworks",
    "EXPERIMENTAL ADVISORY AGENTS",
    "Escalations are review records only unless explicitly authorized by an operator"
)

Write-Host "Checking public dashboard: $BaseUrl/"
$homeResponse = Invoke-WithRetry -Label "GET /" -Action {
    Invoke-WebRequest -Uri "$BaseUrl/" -UseBasicParsing -TimeoutSec 30
}
$body = [string]$homeResponse.Content

foreach ($phrase in $ForbiddenPhrases) {
    if ($body.Contains($phrase)) {
        Write-Error "FAIL: forbidden public-copy phrase is still visible: $phrase"
        exit 1
    }
}

foreach ($phrase in $RequiredPhrases) {
    if (-not $body.Contains($phrase)) {
        Write-Error "FAIL: required safe public-copy phrase is missing: $phrase"
        exit 1
    }
}

Write-Host "Checking health endpoint: $BaseUrl/health"
$healthResponse = Invoke-WithRetry -Label "GET /health" -Action {
    Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec 30
}
if ($healthResponse.StatusCode -lt 200 -or $healthResponse.StatusCode -ge 300) {
    Write-Error "FAIL: /health returned HTTP $($healthResponse.StatusCode)"
    exit 1
}

Write-Host "Checking status endpoint: $BaseUrl/api/status"
$statusResponse = Invoke-WithRetry -Label "GET /api/status" -Action {
    Invoke-WebRequest -Uri "$BaseUrl/api/status" -UseBasicParsing -TimeoutSec 30
}
try {
    $null = $statusResponse.Content | ConvertFrom-Json
}
catch {
    Write-Error "FAIL: /api/status did not return valid JSON: $($_.Exception.Message)"
    exit 1
}

$ForbiddenApiPhrases = @(
    "no_human_override",
    "escalation_is_irreversible",
    "ALGORITHMIC GOVERNANCE",
    "No human board",
    "irreversible after a 24-hour lock"
)

foreach ($endpoint in @("/api/autonomous/status", "/api/autonomous/rules")) {
    Write-Host "Checking autonomous endpoint: $BaseUrl$endpoint"
    $autonomousResponse = Invoke-WithRetry -Label "GET $endpoint" -Action {
        Invoke-WebRequest -Uri "$BaseUrl$endpoint" -UseBasicParsing -TimeoutSec 30
    }
    try {
        $null = $autonomousResponse.Content | ConvertFrom-Json
    }
    catch {
        Write-Error "FAIL: $endpoint did not return valid JSON: $($_.Exception.Message)"
        exit 1
    }
    $autonomousBody = [string]$autonomousResponse.Content
    foreach ($phrase in $ForbiddenApiPhrases) {
        if ($autonomousBody.Contains($phrase)) {
            Write-Error "FAIL: forbidden authority phrase '$phrase' is still present in $endpoint"
            exit 1
        }
    }
}

Write-Host "PASS: public site smoke validation succeeded for $BaseUrl"
