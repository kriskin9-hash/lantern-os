param(
    [string]$ImageName = "hff-smoke:local",
    [string]$ContainerName = "hff-smoke-local",
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"

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

function Test-DockerAvailable {
    try {
        docker version | Out-Null
        return $true
    }
    catch {
        Write-Error "FAIL: Docker is not available or Docker Desktop is not running. Start Docker Desktop, wait for the Linux engine, then rerun this script. Details: $($_.Exception.Message)"
        return $false
    }
}

function Stop-SmokeContainer {
    try {
        docker rm -f $ContainerName 2>$null | Out-Null
    }
    catch {
        # Ignore cleanup failures. The main validation path reports Docker/startup failures explicitly.
    }
}

if (-not (Test-DockerAvailable)) {
    exit 1
}

try {
    Write-Host "Building Docker image: $ImageName"
    docker build -t $ImageName .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL: docker build failed with exit code $LASTEXITCODE"
        exit 1
    }

    Write-Host "Starting container: $ContainerName on port $Port"
    Stop-SmokeContainer
    docker run -d --rm --name $ContainerName -p "${Port}:5000" -e PORT=5000 $ImageName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAIL: docker run failed with exit code $LASTEXITCODE"
        exit 1
    }

    $healthUrl = "http://127.0.0.1:$Port/health"
    $homeUrl = "http://127.0.0.1:$Port/"
    $statusUrl = "http://127.0.0.1:$Port/api/status"

    $healthy = $false
    for ($i = 1; $i -le 30; $i++) {
        try {
            Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5 | Out-Null
            $healthy = $true
            break
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $healthy) {
        docker logs $ContainerName
        Write-Error "FAIL: container did not become healthy at $healthUrl"
        exit 1
    }

    Write-Host "Checking dashboard copy: $homeUrl"
    $homeResponse = Invoke-WebRequest -Uri $homeUrl -UseBasicParsing -TimeoutSec 30
    $body = [string]$homeResponse.Content

    foreach ($phrase in $ForbiddenPhrases) {
        if ($body.Contains($phrase)) {
            Write-Error "FAIL: forbidden public-copy phrase appears in container: $phrase"
            exit 1
        }
    }

    foreach ($phrase in $RequiredPhrases) {
        if (-not $body.Contains($phrase)) {
            Write-Error "FAIL: required safe public-copy phrase is missing from container: $phrase"
            exit 1
        }
    }

    Write-Host "Checking status JSON: $statusUrl"
    $statusResponse = Invoke-WebRequest -Uri $statusUrl -UseBasicParsing -TimeoutSec 30
    try {
        $null = $statusResponse.Content | ConvertFrom-Json
    }
    catch {
        Write-Error "FAIL: /api/status did not return valid JSON: $($_.Exception.Message)"
        exit 1
    }

    Write-Host "PASS: container smoke validation succeeded"
}
finally {
    Stop-SmokeContainer
}
