[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$scriptRoot = Join-Path $Root "scripts"
if (!(Test-Path $scriptRoot)) {
    throw "PowerShell scripts directory was not found: $scriptRoot"
}

$holddScripts = @(
    "Start-GptWebAgent.ps1",
    "Start-GptWebAgent-Continuous.ps1"
)

$archiveRoot = Join-Path $scriptRoot "archive"

$scriptFiles = @(Get-ChildItem -Path $scriptRoot -Filter "*.ps1" -File -Recurse |
    Where-Object { -not $_.FullName.StartsWith($archiveRoot, [System.StringComparison]::OrdinalIgnoreCase) } |
    Where-Object { $_.Name -notin $holddScripts } |
    Sort-Object FullName)

if ($scriptFiles.Count -eq 0) {
    throw "No PowerShell scripts found under $scriptRoot after hold filter"
}

$failures = @()
foreach ($scriptFile in $scriptFiles) {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($scriptFile.FullName, [ref]$tokens, [ref]$parseErrors) | Out-Null

    if ($parseErrors.Count -gt 0) {
        foreach ($parseError in $parseErrors) {
            $failures += [pscustomobject]@{
                Path = $scriptFile.FullName.Replace($Root, "").TrimStart([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
                Line = $parseError.Extent.StartLineNumber
                Column = $parseError.Extent.StartColumnNumber
                Message = $parseError.Message
            }
        }
    }
}

if ($failures.Count -gt 0) {
    $failures | Format-Table -AutoSize | Out-String | Write-Error
    throw "PowerShell parser validation failed for $($failures.Count) parse error(s)."
}

Write-Host "Validated PowerShell syntax for $($scriptFiles.Count) script(s)."
if ($holddScripts.Count -gt 0) {
    Write-Warning "Skipped holdd experimental scripts: $($holddScripts -join ', ')"
}
if (Test-Path -LiteralPath $archiveRoot -PathType Container) {
    Write-Warning "Skipped archived one-off scripts under scripts/archive."
}
