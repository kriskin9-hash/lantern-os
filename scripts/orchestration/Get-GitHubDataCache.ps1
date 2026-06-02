[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$Owner = "alex-place",
    [string]$Repo = "gm-agent-orchestrator",
    [string]$Action = "summary",
    [int]$PrNumber = 0
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

$CacheDir = Join-Path $Root ".github-cache"
if (!(Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
}

$IssuesCachePath = Join-Path $CacheDir "issues.json"
$PrsCachePath = Join-Path $CacheDir "prs.json"
$Script:LastGitHubError = ""
$CacheTtlSeconds = 30

function Get-CacheLastWriteTime {
    param([string]$CachePath)
    if ([string]::IsNullOrWhiteSpace($CachePath) -or -not (Test-Path -LiteralPath $CachePath -PathType Leaf)) { return $null }
    return (Get-Item -LiteralPath $CachePath -ErrorAction Stop).LastWriteTime
}

function Is-CacheValid {
    param([string]$CachePath)
    if (!(Test-Path -LiteralPath $CachePath -PathType Leaf)) { return $false }
    $file = Get-Item -LiteralPath $CachePath -ErrorAction Stop
    $age = (Get-Date) - $file.LastWriteTime
    return $age.TotalSeconds -lt $CacheTtlSeconds
}

function Read-Cache {
    param([string]$CachePath)
    if (!(Test-Path -LiteralPath $CachePath -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $CachePath -Raw | ConvertFrom-Json }
    catch { return $null }
}

function Write-Cache {
    param([string]$CachePath, [object]$Data)
    $json = $Data | ConvertTo-Json -Depth 80 -Compress
    [System.IO.File]::WriteAllText($CachePath, $json, [System.Text.UTF8Encoding]::new($false))
}

function Invoke-GitHubApi {
    param([string]$Query)

    $Script:LastGitHubError = ""

    try {
        $gh = Get-Command gh -ErrorAction SilentlyContinue
        if ($null -eq $gh) {
            $Script:LastGitHubError = "GitHub CLI command not found on PATH: gh"
            return $null
        }

        $output = @(& gh api $Query 2>&1)
        $exitCode = $LASTEXITCODE
        $text = (($output | ForEach-Object { $_.ToString() }) -join "`n").Trim()

        if ($exitCode -ne 0) {
            $Script:LastGitHubError = "GitHub API error for '$Query': $text"
            return $null
        }

        if ([string]::IsNullOrWhiteSpace($text)) {
            return $null
        }

        return $text | ConvertFrom-Json
    }
    catch {
        $Script:LastGitHubError = "Failed to fetch GitHub data for '$Query': $($_.Exception.Message)"
        return $null
    }
}

function Invoke-GitHubApiPaged {
    param(
        [string]$QueryBase,
        [int]$MaxPages = 20
    )

    $items = @()

    for ($page = 1; $page -le $MaxPages; $page++) {
        $separator = $(if ($QueryBase -match "\?") { "&" } else { "?" })
        $query = "${QueryBase}${separator}per_page=100&page=$page"
        $pageData = Invoke-GitHubApi -Query $query

        if (-not [string]::IsNullOrWhiteSpace($Script:LastGitHubError)) {
            return $null
        }

        if ($null -eq $pageData) {
            break
        }

        $pageItems = @($pageData)
        if ($pageItems.Count -eq 0) {
            break
        }

        $items += $pageItems
        if ($pageItems.Count -lt 100) {
            break
        }
    }

    return $items
}

function Get-GitHubIssuesCached {
    if (Is-CacheValid -CachePath $IssuesCachePath) {
        $cached = Read-Cache -CachePath $IssuesCachePath
        if ($null -ne $cached) { return $cached }
    }

    $issues = Invoke-GitHubApiPaged -QueryBase "repos/$Owner/$Repo/issues?state=all&sort=updated&direction=desc"

    if ($null -ne $issues) {
        $simplified = @($issues | ForEach-Object {
            [pscustomobject]@{
                number = $_.number
                title = $_.title
                state = $_.state
                assignee = $(if ($_.assignee) { $_.assignee.login } else { $null })
                labels = @($_.labels | ForEach-Object { $_.name })
                created_at = $_.created_at
                updated_at = $_.updated_at
                url = $_.html_url
            }
        })
        Write-Cache -CachePath $IssuesCachePath -Data $simplified
        return $simplified
    }
    return @()
}

function Get-GitHubPrStatusCached {
    if (Is-CacheValid -CachePath $PrsCachePath) {
        $cached = Read-Cache -CachePath $PrsCachePath
        if ($null -ne $cached) { return $cached }
    }

    $prs = Invoke-GitHubApiPaged -QueryBase "repos/$Owner/$Repo/pulls?state=all&sort=updated&direction=desc"

    if ($null -ne $prs) {
        $simplified = @($prs | ForEach-Object {
            [pscustomobject]@{
                number = $_.number
                title = $_.title
                state = $_.state
                draft = $_.draft
                author = $_.user.login
                created_at = $_.created_at
                updated_at = $_.updated_at
                url = $_.html_url
                review_decision = $(if ($_.PSObject.Properties.Name -contains "review_decision") { $_.review_decision } else { $null })
                merged_at = $_.merged_at
            }
        })
        Write-Cache -CachePath $PrsCachePath -Data $simplified
        return $simplified
    }
    return @()
}

function New-ResultObject {
    param([hashtable]$Payload)

    $ok = [string]::IsNullOrWhiteSpace($Script:LastGitHubError)
    $base = [ordered]@{
        ok = [bool]$ok
        owner = $Owner
        repo = $Repo
        repository = "$Owner/$Repo"
        error = $Script:LastGitHubError
    }

    foreach ($key in $Payload.Keys) {
        $base[$key] = $Payload[$key]
    }

    return [pscustomobject]$base
}

try {
    switch ($Action) {
        "issues" {
            $issues = Get-GitHubIssuesCached
            $result = New-ResultObject -Payload @{
                cached_at = Get-CacheLastWriteTime -CachePath $IssuesCachePath
                count = @($issues).Count
                issues = $issues
            }
        }
        "prs" {
            $prs = Get-GitHubPrStatusCached
            $result = New-ResultObject -Payload @{
                cached_at = Get-CacheLastWriteTime -CachePath $PrsCachePath
                count = @($prs).Count
                prs = $prs
            }
        }
        "pr_detail" {
            if ($PrNumber -le 0) { throw "PrNumber is required for pr_detail action" }
            $pr = Invoke-GitHubApi -Query "repos/$Owner/$Repo/pulls/$PrNumber"
            if ($null -ne $pr) {
                $result = New-ResultObject -Payload @{
                    pr_number  = $PrNumber
                    number     = $pr.number
                    title      = $pr.title
                    state      = $pr.state
                    draft      = $pr.draft
                    body       = $pr.body
                    author     = $pr.user.login
                    head_sha   = $pr.head.sha
                    head_branch = $pr.head.ref
                    base_branch = $pr.base.ref
                    mergeable  = $pr.mergeable
                    mergeable_state = $pr.mergeable_state
                    additions  = $pr.additions
                    deletions  = $pr.deletions
                    changed_files = $pr.changed_files
                    url        = $pr.html_url
                    created_at = $pr.created_at
                    updated_at = $pr.updated_at
                }
            } else {
                $result = New-ResultObject -Payload @{ pr_number = $PrNumber }
            }
        }
        "pr_files" {
            if ($PrNumber -le 0) { throw "PrNumber is required for pr_files action" }
            $files = Invoke-GitHubApiPaged -QueryBase "repos/$Owner/$Repo/pulls/$PrNumber/files"
            if ($null -ne $files) {
                $simplified = @($files | ForEach-Object {
                    [pscustomobject]@{
                        filename  = $_.filename
                        status    = $_.status
                        additions = $_.additions
                        deletions = $_.deletions
                        changes   = $_.changes
                        patch     = $(if ($_.PSObject.Properties.Name -contains "patch") { $_.patch } else { $null })
                    }
                })
                $result = New-ResultObject -Payload @{
                    pr_number = $PrNumber
                    count     = @($simplified).Count
                    files     = $simplified
                }
            } else {
                $result = New-ResultObject -Payload @{ pr_number = $PrNumber; count = 0; files = @() }
            }
        }
        "pr_checks" {
            if ($PrNumber -le 0) { throw "PrNumber is required for pr_checks action" }
            $pr = Invoke-GitHubApi -Query "repos/$Owner/$Repo/pulls/$PrNumber"
            if ($null -ne $pr) {
                $sha = $pr.head.sha
                $checksResult = Invoke-GitHubApi -Query "repos/$Owner/$Repo/commits/$sha/check-runs?per_page=100"
                if ($null -ne $checksResult) {
                    $checks = @($checksResult.check_runs | ForEach-Object {
                        [pscustomobject]@{
                            name         = $_.name
                            status       = $_.status
                            conclusion   = $_.conclusion
                            started_at   = $_.started_at
                            completed_at = $_.completed_at
                            url          = $_.html_url
                        }
                    })
                    $result = New-ResultObject -Payload @{
                        pr_number   = $PrNumber
                        head_sha    = $sha
                        total_count = $checksResult.total_count
                        checks      = $checks
                    }
                } else {
                    $result = New-ResultObject -Payload @{ pr_number = $PrNumber; head_sha = $sha; total_count = 0; checks = @() }
                }
            } else {
                $result = New-ResultObject -Payload @{ pr_number = $PrNumber; total_count = 0; checks = @() }
            }
        }
        "pr_comments" {
            if ($PrNumber -le 0) { throw "PrNumber is required for pr_comments action" }
            $reviewComments = Invoke-GitHubApiPaged -QueryBase "repos/$Owner/$Repo/pulls/$PrNumber/comments"
            $reviewError = $Script:LastGitHubError
            $issueComments = Invoke-GitHubApiPaged -QueryBase "repos/$Owner/$Repo/issues/$PrNumber/comments"
            $issueError = $Script:LastGitHubError
            $Script:LastGitHubError = (($reviewError, $issueError | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join "; ")
            $allReview = @()
            if ($null -ne $reviewComments) {
                $allReview = @($reviewComments | ForEach-Object {
                    [pscustomobject]@{
                        type       = "review"
                        id         = $_.id
                        author     = $_.user.login
                        body       = $_.body
                        path       = $_.path
                        line       = $_.line
                        created_at = $_.created_at
                        url        = $_.html_url
                    }
                })
            }
            $allIssue = @()
            if ($null -ne $issueComments) {
                $allIssue = @($issueComments | ForEach-Object {
                    [pscustomobject]@{
                        type       = "issue"
                        id         = $_.id
                        author     = $_.user.login
                        body       = $_.body
                        path       = $null
                        line       = $null
                        created_at = $_.created_at
                        url        = $_.html_url
                    }
                })
            }
            $combined = @($allReview) + @($allIssue)
            $result = New-ResultObject -Payload @{
                pr_number       = $PrNumber
                review_comments = @($allReview).Count
                issue_comments  = @($allIssue).Count
                total           = $combined.Count
                comments        = $combined
            }
        }
        default {
            $issues = Get-GitHubIssuesCached
            $issuesError = $Script:LastGitHubError
            $prs = Get-GitHubPrStatusCached
            $prsError = $Script:LastGitHubError
            $Script:LastGitHubError = (($issuesError, $prsError | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join "; ")
            $result = New-ResultObject -Payload @{
                issues = [pscustomobject]@{
                    count = @($issues).Count
                    open = @($issues | Where-Object { $_.state -eq "open" }).Count
                    cached_at = Get-CacheLastWriteTime -CachePath $IssuesCachePath
                    error = $issuesError
                }
                prs = [pscustomobject]@{
                    count = @($prs).Count
                    open = @($prs | Where-Object { $_.state -eq "open" }).Count
                    cached_at = Get-CacheLastWriteTime -CachePath $PrsCachePath
                    error = $prsError
                }
            }
        }
    }
}
catch {
    $result = [pscustomobject]@{
        ok = $false
        owner = $Owner
        repo = $Repo
        repository = "$Owner/$Repo"
        error = $_.Exception.Message
        count = 0
    }
}

[Console]::Out.WriteLine(($result | ConvertTo-Json -Depth 80 -Compress))
