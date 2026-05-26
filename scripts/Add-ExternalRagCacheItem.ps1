param(
    [Parameter(Mandatory = $true)]
    [string]$Topic,
    [Parameter(Mandatory = $true)]
    [string]$Claim,
    [string]$SourceUrl = "",
    [string]$SourceTitle = "",
    [ValidateSet("official_source", "web_secondary", "external_llm", "operator_asserted")]
    [string]$SourceType = "external_llm",
    [ValidateSet("summary_only", "public_domain", "creative_commons", "unknown")]
    [string]$RightsState = "summary_only",
    [ValidateSet("official_source", "web_secondary", "operator_asserted", "projection", "unknown")]
    [string]$EvidenceClass = "operator_asserted",
    [double]$Confidence = 0.5,
    [ValidateSet("promote", "candidate", "hold", "reject")]
    [string]$Decision = "candidate",
    [Parameter(Mandatory = $true)]
    [string]$CompressedSummary,
    [string]$Cache = "data/rag-intake/external-llm-web-cache/cache.jsonl"
)

$ErrorActionPreference = "Stop"

if ($CompressedSummary.Length -gt 1200) {
    throw "CompressedSummary is too long. Keep external RAG cache items under 1200 characters."
}

if ($Claim.Length -gt 500) {
    throw "Claim is too long. Keep claims under 500 characters."
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$cachePath = Join-Path $root $Cache
$cacheDir = Split-Path -Parent $cachePath
New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null

$record = [ordered]@{
    timestamp = (Get-Date).ToString("o")
    topic = $Topic
    claim = $Claim
    sourceUrl = $SourceUrl
    sourceTitle = $SourceTitle
    sourceType = $SourceType
    rightsState = $RightsState
    evidenceClass = $EvidenceClass
    confidence = $Confidence
    decision = $Decision
    compressedSummary = $CompressedSummary
}

($record | ConvertTo-Json -Compress) | Add-Content -LiteralPath $cachePath -Encoding UTF8
Write-Output $cachePath
