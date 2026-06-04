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

# Find rooms directory
$roomsDir = Join-Path $projectPath "rooms"
$rooms = @()
$issues = @()

if (Test-Path $roomsDir) {
    Get-ChildItem -Path $roomsDir -Filter "*.yy" -File | ForEach-Object {
        $roomFile = $_
        try {
            $content = Get-Content $roomFile.FullName -Raw
            # Remove trailing commas (GameMaker format)
            $content = $content -replace ',\s*}', '}' -replace ',\s*\]', ']'
            $roomData = $content | ConvertFrom-Json

            # Count instances and layers
            $instanceCount = @($roomData.instances).Count
            $layerCount = @($roomData.layers).Count

            $room = [pscustomobject]@{
                name = $roomData.name
                width = $roomData.roomSettings.Width
                height = $roomData.roomSettings.Height
                instanceCount = $instanceCount
                layerCount = $layerCount
                file = $roomFile.Name
                valid = $instanceCount -ge 0 -and $layerCount -gt 0
            }

            $rooms += $room

            # Check for issues
            if ($layerCount -eq 0) {
                $issues += "Room '$($roomData.name)' has no layers"
            }
        }
        catch {
            $issues += "Failed to parse room '$($roomFile.Name)': $($_.Exception.Message)"
        }
    }
}

# Try to use gm_agent.py if available for more detailed validation
$gmAgentPath = Join-Path $projectPath "tools\gamemaker-room-editor\scripts\gm_agent.py"
$validation = @()

if (Test-Path $gmAgentPath) {
    try {
        $output = & python $gmAgentPath list-rooms --project (Join-Path $projectPath "*.yyp" | Get-ChildItem | Select-Object -First 1 | Select-Object -ExpandProperty Name) 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($output) {
            $validation = $output | Select-Object -First 5
        }
    }
    catch {
        # gm_agent.py may not be available or fail, that's ok
    }
}

$result = [pscustomobject]@{
    ok = $true
    projectName = $ProjectName
    totalRooms = @($rooms).Count
    validRooms = @($rooms | Where-Object { $_.valid }).Count
    issueCount = @($issues).Count
    rooms = @($rooms)
    issues = @($issues | Select-Object -First 20)
    gmAgentAvailable = Test-Path $gmAgentPath
    status = $(if (@($issues).Count -gt 0) { "warning" } else { "healthy" })
}

return $result | ConvertTo-Json -Depth 80
