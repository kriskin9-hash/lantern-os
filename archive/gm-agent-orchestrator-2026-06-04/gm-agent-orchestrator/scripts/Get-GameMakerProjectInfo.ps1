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

# Find .yyp file
$yypFile = Get-ChildItem -Path $projectPath -Filter "*.yyp" -File | Select-Object -First 1
if (!$yypFile) {
    throw "No .yyp file found in $projectPath"
}

# Parse .yyp file (GameMaker uses relaxed JSON with trailing commas)
try {
    $content = Get-Content $yypFile.FullName -Raw
    # Remove trailing commas (GameMaker format)
    $content = $content -replace ',\s*}', '}' -replace ',\s*\]', ']'
    $yyp = $content | ConvertFrom-Json
}
catch {
    throw "Failed to parse .yyp file: $($_.Exception.Message)"
}

# Extract project metadata
$resourceCount = 0
if ($yyp.resources -is [array]) { $resourceCount = @($yyp.resources).Count }
elseif ($yyp.resources) { $resourceCount = 1 }

$result = [pscustomobject]@{
    ok = $true
    name = $ProjectName
    displayName = $yyp.'%Name'
    resourceCount = $resourceCount
    creationTime = $yypFile.CreationTime
    lastModified = $yypFile.LastWriteTime
    path = $projectPath
}

return $result | ConvertTo-Json -Depth 80
