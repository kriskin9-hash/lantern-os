[CmdletBinding()]
param(
    [string]$Root = "",
    [ValidateSet("alex-place")]
    [string]$Owner = "alex-place",
    [ValidateSet("gm-agent-orchestrator")]
    [string]$Repo = "gm-agent-orchestrator",
    [Parameter(Mandatory)]
    [long]$CommentId,
    [string]$Body = "",
    [string]$BodyPath = "",
    [switch]$DryRun,
    [string]$ExpectedContains = "",
    [int]$MaxBodyLength = 65000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$Repository = "$Owner/$Repo"
if ($Repository -ne "alex-place/gm-agent-orchestrator") {
    throw "Refusing to update issue comment outside alex-place/gm-agent-orchestrator. Requested: $Repository"
}

function New-Result {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$ErrorMessage = "",
        [object]$Extra = $null
    )

    $payload = [ordered]@{
        ok = $Ok
        state = $State
        dryRun = [bool]$DryRun
        owner = $Owner
        repo = $Repo
        repository = $Repository
        commentId = $CommentId
        error = $ErrorMessage
        generatedAt = (Get-Date).ToString("o")
    }

    if ($null -ne $Extra) {
        foreach ($property in $Extra.PSObject.Properties) {
            $payload[$property.Name] = $property.Value
        }
    }

    [Console]::Out.WriteLine(([pscustomobject]$payload | ConvertTo-Json -Depth 80 -Compress))
}

try {
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if ($null -eq $gh) {
        New-Result -Ok $false -State "blocked_missing_gh" -ErrorMessage "GitHub CLI command not found on PATH: gh"
        exit 0
    }

    if (-not [string]::IsNullOrWhiteSpace($BodyPath)) {
        $resolvedBodyPath = Resolve-Path -LiteralPath $BodyPath -ErrorAction Stop
        $Body = Get-Content -LiteralPath $resolvedBodyPath -Raw -ErrorAction Stop
    }

    if ([string]::IsNullOrWhiteSpace($Body)) {
        New-Result -Ok $false -State "blocked_missing_body" -ErrorMessage "Provide -Body or -BodyPath."
        exit 0
    }

    if ($Body.Length -gt $MaxBodyLength) {
        New-Result -Ok $false -State "blocked_body_too_large" -ErrorMessage "Body length $($Body.Length) exceeds MaxBodyLength $MaxBodyLength."
        exit 0
    }

    $commentPath = "repos/$Owner/$Repo/issues/comments/$CommentId"
    $fetchOutput = @(& gh api $commentPath 2>&1)
    $fetchExit = $LASTEXITCODE
    $fetchText = (($fetchOutput | ForEach-Object { $_.ToString() }) -join "`n").Trim()

    if ($fetchExit -ne 0) {
        New-Result -Ok $false -State "blocked_fetch_failed" -ErrorMessage $fetchText
        exit 0
    }

    $existing = $fetchText | ConvertFrom-Json
    if ($existing.html_url -notmatch "github\.com/$([regex]::Escape($Owner))/$([regex]::Escape($Repo))/") {
        New-Result -Ok $false -State "blocked_repo_mismatch" -ErrorMessage "Fetched comment URL does not belong to ${Repository}: $($existing.html_url)"
        exit 0
    }

    if (-not [string]::IsNullOrWhiteSpace($ExpectedContains) -and ([string]$existing.body) -notlike "*$ExpectedContains*") {
        New-Result -Ok $false -State "blocked_expected_text_missing" -ErrorMessage "Existing comment body did not contain ExpectedContains marker."
        exit 0
    }

    $bodySha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
        $hash = [BitConverter]::ToString($bodySha.ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $bodySha.Dispose()
    }

    $extra = [pscustomobject]@{
        commentUrl = $existing.html_url
        previousLength = ([string]$existing.body).Length
        newLength = $Body.Length
        newBodySha256 = $hash
    }

    if ($DryRun) {
        New-Result -Ok $true -State "dry_run" -Extra $extra
        exit 0
    }

    $payload = @{ body = $Body } | ConvertTo-Json -Compress
    $tempPayload = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllText($tempPayload, $payload, [System.Text.UTF8Encoding]::new($false))
        $updateOutput = @(& gh api --method PATCH $commentPath --input $tempPayload 2>&1)
        $updateExit = $LASTEXITCODE
        $updateText = (($updateOutput | ForEach-Object { $_.ToString() }) -join "`n").Trim()
        if ($updateExit -ne 0) {
            New-Result -Ok $false -State "blocked_update_failed" -ErrorMessage $updateText -Extra $extra
            exit 0
        }
        $updated = $updateText | ConvertFrom-Json
        $extra | Add-Member -NotePropertyName updatedAt -NotePropertyValue $updated.updated_at
        New-Result -Ok $true -State "updated" -Extra $extra
    }
    finally {
        Remove-Item -LiteralPath $tempPayload -Force -ErrorAction SilentlyContinue
    }
}
catch {
    New-Result -Ok $false -State "failed_exception" -ErrorMessage $_.Exception.Message
}
