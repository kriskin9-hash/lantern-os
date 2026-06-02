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

# Find sprites directory
$spritesDir = Join-Path $projectPath "sprites"
$sprites = @()
$issues = @()

if (Test-Path $spritesDir) {
    Get-ChildItem -Path $spritesDir -Directory | ForEach-Object {
        $spriteDir = $_
        $yy = Get-ChildItem -Path $spriteDir.FullName -Filter "*.yy" -File | Select-Object -First 1

        if ($yy) {
            try {
                $content = Get-Content $yy.FullName -Raw
                # Remove trailing commas (GameMaker format)
                $content = $content -replace ',\s*}', '}' -replace ',\s*\]', ']'
                $spriteData = $content | ConvertFrom-Json

                # Check for texture groups
                $textureGroups = $spriteData.textureGroups | Measure-Object | Select-Object -ExpandProperty Count
                $frameCount = @($spriteData.frames).Count

                # Look for actual image files
                $pngFiles = Get-ChildItem -Path $spriteDir.FullName -Filter "*.png" -File | Measure-Object | Select-Object -ExpandProperty Count

                $sprite = [pscustomobject]@{
                    name = $spriteDir.Name
                    frameCount = $frameCount
                    width = $spriteData.width
                    height = $spriteData.height
                    pngCount = $pngFiles
                    textureGroups = $textureGroups
                    valid = $frameCount -gt 0 -and $pngFiles -gt 0
                }

                $sprites += $sprite

                # Check for issues
                if ($frameCount -eq 0) {
                    $issues += "Sprite '$($spriteDir.Name)' has no frames"
                }
                if ($pngFiles -eq 0) {
                    $issues += "Sprite '$($spriteDir.Name)' has no PNG files"
                }
            }
            catch {
                $issues += "Failed to parse sprite '$($spriteDir.Name)': $($_.Exception.Message)"
            }
        }
    }
}

$result = [pscustomobject]@{
    ok = $true
    projectName = $ProjectName
    totalSprites = @($sprites).Count
    validSprites = @($sprites | Where-Object { $_.valid }).Count
    issueCount = @($issues).Count
    sprites = @($sprites)
    issues = @($issues | Select-Object -First 20)
    status = $(if (@($issues).Count -gt 0) { "warning" } else { "healthy" })
}

return $result | ConvertTo-Json -Depth 80
