param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$OutputDir = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "data\internal-rag-house"),
    [switch]$IncludeFileBodies,
    [int]$MaxBodyBytes = 200000
)

$ErrorActionPreference = "Stop"

$generatedAt = (Get-Date).ToString("o")
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$repoRoot = (Resolve-Path $Root).Path
$houseFile = Join-Path $OutputDir "LANTERN-OS-INTERNAL-HOUSE-RAG.flat.md"
$manifestFile = Join-Path $OutputDir "RAG-HOUSE-MANIFEST.json"
$hashFile = Join-Path $OutputDir "RAG-HOUSE-MANIFEST.sha256"

$includeGlobs = @(
    "README.md",
    "AGENTS.md",
    "QUICK-START.md",
    "docs/*.md",
    "docs/**/*.md",
    "manifests/*.md",
    "manifests/**/*.md",
    "reports/*.md",
    "data/automation/*.json",
    "data/automation/*.md",
    "data/arc-reactor/*.json",
    "skills/*/SKILL.md",
    "skills/**/*.md",
    "scripts/*.ps1",
    "data/world-model/*.jsonl",
    "references/*.md"
)

$excludeFragments = @(
    "\.git\",
    "node_modules",
    "dist\",
    "build\",
    "coverage\",
    ".env",
    "secrets",
    "private",
    "PII",
    "Pii"
)

function Test-IncludedPath {
    param([string]$RelativePath)

    foreach ($fragment in $excludeFragments) {
        if ($RelativePath -like "*$fragment*") {
            return $false
        }
    }

    foreach ($glob in $includeGlobs) {
        if ($RelativePath -like $glob) {
            return $true
        }
    }

    return $false
}

function Get-FileSha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

$allFiles = Get-ChildItem -LiteralPath $repoRoot -File -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($repoRoot.Length).TrimStart("\").Replace("/", "\")
    if (Test-IncludedPath -RelativePath $relative) {
        [pscustomobject]@{
            path = $relative.Replace("\", "/")
            fullName = $_.FullName
            length = $_.Length
            sha256 = Get-FileSha256 -Path $_.FullName
            modifiedUtc = $_.LastWriteTimeUtc.ToString("o")
            evidenceClass = "local_verified"
        }
    }
} | Where-Object { $_ -ne $null } | Sort-Object path

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# Lantern OS Internal House RAG") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("Generated: $generatedAt") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("This flat file is an internal, source-linked RAG house index for Lantern OS. It records file paths, hashes, evidence classes, and optional file bodies. It does not delete or move source files.") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("## Boundaries") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("- Internal storage only.") | Out-Null
$lines.Add("- No secrets, .env files, private folders, or raw PIID should be imported.") | Out-Null
$lines.Add("- Source repositories remain authoritative until a promotion commit is reviewed.") | Out-Null
$lines.Add("- Moving code means copy/promote with hashes first, then retire old source paths only after validation.") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("## Included files") | Out-Null
$lines.Add("") | Out-Null

foreach ($file in $allFiles) {
    $lines.Add("### $($file.path)") | Out-Null
    $lines.Add("") | Out-Null
    $lines.Add("- evidenceClass: $($file.evidenceClass)") | Out-Null
    $lines.Add("- bytes: $($file.length)") | Out-Null
    $lines.Add("- sha256: $($file.sha256)") | Out-Null
    $lines.Add("- modifiedUtc: $($file.modifiedUtc)") | Out-Null

    if ($IncludeFileBodies) {
        if ($file.length -le $MaxBodyBytes) {
            $extension = [System.IO.Path]::GetExtension($file.path).TrimStart(".")
            if ([string]::IsNullOrWhiteSpace($extension)) { $extension = "text" }
            $body = Get-Content -LiteralPath $file.fullName -Raw -ErrorAction Stop
            $lines.Add("") | Out-Null
            $lines.Add("````$extension") | Out-Null
            $lines.Add($body.TrimEnd()) | Out-Null
            $lines.Add("````") | Out-Null
        }
        else {
            $lines.Add("- body: skipped_large_file") | Out-Null
        }
    }

    $lines.Add("") | Out-Null
}

$lines | Set-Content -LiteralPath $houseFile -Encoding UTF8

$manifest = [ordered]@{
    generatedAt = $generatedAt
    root = $repoRoot
    outputDir = $OutputDir
    includeFileBodies = [bool]$IncludeFileBodies
    maxBodyBytes = $MaxBodyBytes
    fileCount = @($allFiles).Count
    files = @($allFiles | ForEach-Object {
        [ordered]@{
            path = $_.path
            bytes = $_.length
            sha256 = $_.sha256
            modifiedUtc = $_.modifiedUtc
            evidenceClass = $_.evidenceClass
        }
    })
    boundaries = [ordered]@{
        noDeletion = $true
        noSourceRepoMutation = $true
        noSecrets = $true
        sourceReposRemainAuthoritative = $true
    }
}

$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestFile -Encoding UTF8
Get-FileHash -Algorithm SHA256 -LiteralPath $houseFile, $manifestFile | ForEach-Object {
    "$($_.Hash.ToLowerInvariant())  $([System.IO.Path]::GetFileName($_.Path))"
} | Set-Content -LiteralPath $hashFile -Encoding UTF8

[pscustomobject]@{
    generatedAt = $generatedAt
    houseFile = $houseFile
    manifestFile = $manifestFile
    hashFile = $hashFile
    fileCount = @($allFiles).Count
} | ConvertTo-Json -Depth 4
