# Lantern Deployment Validation using curl
# Direct shell-based validation avoiding Python connection issues

Write-Host "`n=================================="
Write-Host "LANTERN DEPLOYMENT VALIDATION"
Write-Host "==================================`n"

$baseUrl = "http://127.0.0.1:5000"
$results = @()
$timestamp = Get-Date -Format "o"

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Path,
        [string]$Body = $null
    )

    $url = "$baseUrl$Path"
    $elapsed = Measure-Command {
        if ($Method -eq "GET") {
            $response = curl -s -w "`n%{http_code}" "$url" 2>&1
        } else {
            if ($Body) {
                $response = curl -s -X POST -H "Content-Type: application/json" -d "$Body" -w "`n%{http_code}" "$url" 2>&1
            } else {
                $response = curl -s -X POST -w "`n%{http_code}" "$url" 2>&1
            }
        }
    }

    $statusCode = [int]($response[-1])
    $content = $response[0..($response.Length - 2)] -join "`n"

    $status = "PASS"
    $details = ""

    if ($statusCode -eq 200 -or $statusCode -eq 201) {
        if ($Method -eq "GET") {
            $details = "Status $statusCode, response received"
        } else {
            $details = "Status $statusCode, message accepted"
        }
    } elseif ($statusCode -eq 404) {
        $status = "FAIL"
        $details = "Endpoint not found (404)"
    } elseif ($statusCode -eq 0) {
        $status = "ERROR"
        $details = "Connection failed"
    } else {
        $status = "FAIL"
        $details = "Unexpected status $statusCode"
    }

    Write-Host "[$status] $Name`: $details (${elapsed.TotalMilliseconds}ms)"

    $results += @{
        test = $Name
        status = $status
        details = $details
        path = $Path
        method = $Method
        statusCode = $statusCode
        latencyMs = $elapsed.TotalMilliseconds
        timestamp = (Get-Date -Format "o")
    }
}

# Run tests
Test-Endpoint -Name "Root Interface" -Method "GET" -Path "/"
Test-Endpoint -Name "Chat API (GET)" -Method "GET" -Path "/api/chat"
Test-Endpoint -Name "Chat API (POST)" -Method "POST" -Path "/api/chat" -Body '{"content":"Validation test"}'
Test-Endpoint -Name "Audio API" -Method "GET" -Path "/api/audio"

# Summary
Write-Host "`n==================================`n"

$passed = ($results | Where-Object { $_.status -eq "PASS" }).Count
$total = $results.Count

Write-Host "SUMMARY"
Write-Host "======="
Write-Host "Total tests: $total"
Write-Host "Passed: $passed"
Write-Host "Failed/Error: $($total - $passed)"
Write-Host "Success rate: $([math]::Round(($passed/$total)*100))%`n"

# Export as JSON
$report = @{
    deployment_validation = @{
        timestamp = $timestamp
        summary = @{
            total_tests = $total
            passed = $passed
            failed_or_error = $total - $passed
            success_rate = [math]::Round(($passed/$total)*100)
        }
        results = $results
    }
}

$reportJson = ConvertTo-Json -InputObject $report -Depth 10
$reportJson | Out-File -FilePath "D:\tmp\lantern-os\validation_report.json" -Encoding UTF8

Write-Host "[OK] Full report saved to: D:\tmp\lantern-os\validation_report.json`n"

exit 0
