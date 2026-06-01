[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,

    [Parameter()]
    [string[]]$ArgumentList = @(),

    [Parameter()]
    [string]$WorkingDirectory = (Get-Location).Path,

    [Parameter()]
    [string]$StdOutPath = "",

    [Parameter()]
    [string]$StdErrPath = "",

    [switch]$PassThru
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($FilePath)) {
    throw "FilePath is required."
}

if (-not (Test-Path $WorkingDirectory)) {
    throw "WorkingDirectory was not found: $WorkingDirectory"
}

function Resolve-OptionalOutputPath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }

    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    return $Path
}

function ConvertTo-ProcessArgumentString {
    param([string[]]$Arguments)

    $escaped = foreach ($argument in @($Arguments)) {
        if ($null -eq $argument) { continue }

        $text = [string]$argument
        if ($text -eq "") { '""'; continue }

        if ($text -notmatch '[\s"]') {
            $text
            continue
        }

        '"' + ($text -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
    }

    return ($escaped -join ' ')
}

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $FilePath
$startInfo.WorkingDirectory = $WorkingDirectory
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.Arguments = ConvertTo-ProcessArgumentString -Arguments $ArgumentList

$resolvedOut = Resolve-OptionalOutputPath -Path $StdOutPath
$resolvedErr = Resolve-OptionalOutputPath -Path $StdErrPath

if (-not [string]::IsNullOrWhiteSpace($resolvedOut)) {
    $startInfo.RedirectStandardOutput = $true
}

if (-not [string]::IsNullOrWhiteSpace($resolvedErr)) {
    $startInfo.RedirectStandardError = $true
}

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $startInfo

if (-not $process.Start()) {
    throw "Failed to start process: $FilePath"
}

if ($PassThru) {
    $process
}
else {
    [pscustomobject]@{
        ok = $true
        processId = $process.Id
        filePath = $FilePath
        arguments = $startInfo.Arguments
        workingDirectory = $WorkingDirectory
        stdout = $resolvedOut
        stderr = $resolvedErr
    }
}
