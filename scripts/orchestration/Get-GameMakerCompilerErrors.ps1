[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$ProjectName = "child-of-levistus"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

# Load project config
$configPath = Join-Path $Root "config\projects.json"
if (!(Test-Path $configPath)) {
    throw "Projects config not found: $configPath"
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$project = $config.projects | Where-Object { $_.name -eq $ProjectName }
if (!$project) {
    throw "Project not found: $ProjectName"
}

$projectPath = $project.repoPath
if (!(Test-Path $projectPath)) {
    throw "Project path not found: $projectPath"
}

# Find most recent build/quality check logs
$reportDir = Join-Path $projectPath ".github\reports\local"
$errors = @()
$warnings = @()
$summary = $null

if (Test-Path $reportDir) {
    # Get the latest report
    $latestReport = Get-ChildItem -Path $reportDir -Directory | Sort-Object Name -Descending | Select-Object -First 1

    if ($latestReport) {
        $consoleLogPath = Join-Path $latestReport.FullName "console.log"

        if (Test-Path $consoleLogPath) {
            $content = Get-Content $consoleLogPath -Raw
            $summary = $content.Split("`n") | Select-Object -First 3 -ErrorAction SilentlyContinue

            # Parse for error patterns
            $lines = $content.Split("`n")
            $lines | ForEach-Object {
                if ($_ -match "error|Error|ERROR" -and $_ -notmatch "^Quality check") {
                    $errors += $_
                }
                elseif ($_ -match "warning|Warning|WARNING") {
                    $warnings += $_
                }
            }
        }
    }
}

# Also check for GML syntax issues by scanning source files
$gmlFiles = Get-ChildItem -Path (Join-Path $projectPath "scripts", "objects") -Filter "*.gml" -Recurse -ErrorAction SilentlyContinue

$gmlErrors = @()
$gmlFiles | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $lineNo = 1

    $content.Split("`n") | ForEach-Object {
        # Check for common patterns
        if ($_ -match "dlobal\." -or $_ -match "unkown" -or $_ -match "instance_nearest\(\)" -and $_ -notmatch "//") {
            $gmlErrors += [pscustomobject]@{
                file = $_.FullName.Replace($projectPath, "")
                line = $lineNo
                pattern = $_
                issue = "Potential syntax/pattern issue"
            }
        }
        $lineNo++
    }
}

$result = [pscustomobject]@{
    ok = $true
    projectName = $ProjectName
    compileStatus = $(if (@($errors).Count -gt 0) { "error" } elseif (@($warnings).Count -gt 0) { "warning" } else { "success" })
    errorCount = @($errors).Count
    warningCount = @($warnings).Count
    gmlIssueCount = @($gmlErrors).Count
    errors = @($errors | Select-Object -First 20)
    warnings = @($warnings | Select-Object -First 10)
    gmlIssues = @($gmlErrors | Select-Object -First 10)
    lastCheckTime = $(if ($latestReport) { $latestReport.CreationTime } else { $null })
    summary = if ($summary) { [string]::Join("`n", $summary).Trim() } else { "No build reports found" }
}

return $result | ConvertTo-Json -Depth 80
