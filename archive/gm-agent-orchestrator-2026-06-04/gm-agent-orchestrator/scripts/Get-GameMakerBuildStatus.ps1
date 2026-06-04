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

# Helper to invoke a script and parse JSON
function Invoke-GameMakerScript {
    param([string]$ScriptPath, [string]$ProjectName)
    try {
        $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath -Root $Root -ProjectName $ProjectName 2>&1)
        $text = ($output | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { return $null }
        return $text | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        return $null
    }
}

# Invoke all the GameMaker tools
$projectInfo = Invoke-GameMakerScript -ScriptPath (Join-Path $Root "scripts\Get-GameMakerProjectInfo.ps1") -ProjectName $ProjectName
$compilerErrors = Invoke-GameMakerScript -ScriptPath (Join-Path $Root "scripts\Get-GameMakerCompilerErrors.ps1") -ProjectName $ProjectName
$spriteStatus = Invoke-GameMakerScript -ScriptPath (Join-Path $Root "scripts\Get-GameMakerSpriteAssetStatus.ps1") -ProjectName $ProjectName
$roomStatus = Invoke-GameMakerScript -ScriptPath (Join-Path $Root "scripts\Get-GameMakerRoomEditorStatus.ps1") -ProjectName $ProjectName

# Aggregate status
$overallStatus = "healthy"
$issues = @()
$checks = @()

if ($projectInfo) {
    $checks += [pscustomobject]@{ check = "project_info"; status = "ok"; details = $projectInfo }
}

if ($compilerErrors) {
    $checks += [pscustomobject]@{ check = "compiler"; status = $compilerErrors.compileStatus; errorCount = $compilerErrors.errorCount; warningCount = $compilerErrors.warningCount }
    if ($compilerErrors.compileStatus -eq "error") { $overallStatus = "error" }
    if ($compilerErrors.compileStatus -eq "warning" -and $overallStatus -eq "healthy") { $overallStatus = "warning" }
}

if ($spriteStatus) {
    $checks += [pscustomobject]@{ check = "sprites"; status = $spriteStatus.status; validSprites = $spriteStatus.validSprites; totalSprites = $spriteStatus.totalSprites; issues = @($spriteStatus.issues) }
    if ($spriteStatus.issueCount -gt 0 -and $overallStatus -ne "error") { $overallStatus = "warning" }
}

if ($roomStatus) {
    $checks += [pscustomobject]@{ check = "rooms"; status = $roomStatus.status; validRooms = $roomStatus.validRooms; totalRooms = $roomStatus.totalRooms; issues = @($roomStatus.issues) }
    if ($roomStatus.issueCount -gt 0 -and $overallStatus -ne "error") { $overallStatus = "warning" }
}

$result = [pscustomobject]@{
    ok = $true
    projectName = $ProjectName
    buildStatus = $overallStatus
    checks = @($checks)
    summary = [pscustomobject]@{
        project = $projectInfo
        compiler = $compilerErrors
        sprites = $spriteStatus
        rooms = $roomStatus
    }
    generatedAt = Get-Date -Format "o"
}

return $result | ConvertTo-Json -Depth 80
