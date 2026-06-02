[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$OutputDir = "",
    [switch]$JsonOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $Root "reports\dashboard"
}
elseif (-not [System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputDir = Join-Path $Root $OutputDir
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Invoke-CapturedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $Root,
        [int]$TimeoutSeconds = 60
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $out = "$temp.out"
    $err = "$temp.err"

    try {
        $process = Start-Process -FilePath $FilePath `
            -ArgumentList $Arguments `
            -WorkingDirectory $WorkingDirectory `
            -WindowStyle Hidden `
            -PassThru `
            -RedirectStandardOutput $out `
            -RedirectStandardError $err

        $done = $process.WaitForExit($TimeoutSeconds * 1000)
        if (-not $done) {
            try { $process.Kill() } catch {}
        }

        $stdout = if (Test-Path -LiteralPath $out) { Get-Content -LiteralPath $out -Raw } else { "" }
        $stderr = if (Test-Path -LiteralPath $err) { Get-Content -LiteralPath $err -Raw } else { "" }

        return [pscustomobject]@{
            exitCode = if ($done) { $process.ExitCode } else { $null }
            timedOut = -not $done
            stdout = $stdout
            stderr = $stderr
            combined = ("$stdout`n$stderr").Trim()
        }
    }
    finally {
        Remove-Item -LiteralPath $temp, $out, $err -Force -ErrorAction SilentlyContinue
    }
}

function ConvertTo-SafeText {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }

    $text = [string]$Value
    $text = $text -replace '[A-Za-z]:\\[^\s''"<>]+', 'local workspace'
    $text = $text -replace '(?:tasks|logs|scripts|config|reports)\\[^\s''"<>]+', 'internal item'
    $text = $text -replace '[A-Za-z0-9._-]+\.(?:ps1|md|json|log|jsonl)', 'internal item'
    $text = $text -replace '(?i)codex-main|claude-main|deepseek-main|gemini-main|gemini-flash|gemini-lite|headless-2|headless|autopilot|control-actions', 'team member'
    $text = $text -replace '(?i)codex|claude|deepseek|gemini|openhands|openai|anthropic|google', 'provider'
    $text = $text -replace '(?i)NativeCommandError|RemoteException|FullyQualifiedErrorId|PowerShell|cmdlet|stderr|stdout', 'tooling detail'
    $text = $text -replace '\s+', ' '
    return $text.Trim()
}

function ConvertTo-HtmlText {
    param([string]$Value)
    return [System.Net.WebUtility]::HtmlEncode((ConvertTo-SafeText -Value $Value))
}

function Get-PropertyValue {
    param([object]$Object, [string]$Name, $Default = $null)
    if ($null -eq $Object) { return $Default }
    if ($null -eq $Object.PSObject.Properties[$Name]) { return $Default }
    return $Object.PSObject.Properties[$Name].Value
}

function Get-CountValue {
    param([object]$Counts, [string]$Name)
    $value = Get-PropertyValue -Object $Counts -Name $Name -Default 0
    if ($null -eq $value) { return 0 }
    return [int]$value
}

function ConvertTo-PublicRole {
    param([object]$Slot)

    $name = [string](Get-PropertyValue -Object $Slot -Name "name" -Default "")
    $role = [string](Get-PropertyValue -Object $Slot -Name "role" -Default "")
    $agent = [string](Get-PropertyValue -Object $Slot -Name "agent" -Default "")
    $combined = "$name $role $agent".ToLowerInvariant()

    if ($combined -match "research") { return "Research helper" }
    if ($combined -match "review") { return "Review helper" }
    if ($combined -match "implementation|headless") { return "Implementation helper" }
    if ($combined -match "automation|autopilot|control") { return "Automation" }
    if ($combined -match "coordinator") { return "Coordinator" }
    return "Background worker"
}

function ConvertTo-SafeCategory {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return "No action needed" }
    $value = $Text.ToLowerInvariant()

    if ($value -match "server|connection|endpoint|mcp|404|not found") { return "Service connection needs review" }
    if ($value -match "quota|usage|rate|token|capacity|limit|429") { return "Provider capacity unavailable" }
    if ($value -match "runner|native|script|command|executable|path|tool|validation") { return "Automation runner needs review" }
    if ($value -match "worktree|workspace|git|merge|pull|branch|checkout|dirty") { return "Local workspace needs review" }
    if ($value -match "config|json|schema|auth|credential|login|sign") { return "Tooling configuration needs review" }

    return "Needs review"
}

function Get-SlotAttentionText {
    param([object]$Slot)

    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($name in @("statusText")) {
        $value = Get-PropertyValue -Object $Slot -Name $name -Default ""
        if (-not [string]::IsNullOrWhiteSpace([string]$value)) { $parts.Add([string]$value) }
    }

    $blocker = Get-PropertyValue -Object $Slot -Name "blocker" -Default $null
    if ($null -ne $blocker) {
        foreach ($name in @("kind", "label", "nextAction")) {
            $value = Get-PropertyValue -Object $blocker -Name $name -Default ""
            if (-not [string]::IsNullOrWhiteSpace([string]$value)) { $parts.Add([string]$value) }
        }
    }

    $nextAction = Get-PropertyValue -Object $Slot -Name "nextAction" -Default $null
    if ($null -ne $nextAction) {
        foreach ($name in @("action", "blockedBy")) {
            $value = Get-PropertyValue -Object $nextAction -Name $name -Default ""
            if (-not [string]::IsNullOrWhiteSpace([string]$value)) { $parts.Add([string]$value) }
        }
    }

    return ($parts -join " ")
}

function Get-SafeTaskSummary {
    param([object[]]$Tasks, [int]$Limit = 5)

    return @($Tasks | Select-Object -First $Limit | ForEach-Object {
        [pscustomobject]@{
            title = ConvertTo-SafeText -Value ([string](Get-PropertyValue -Object $_ -Name "title" -Default "Work item"))
            issue = Get-PropertyValue -Object $_ -Name "issue" -Default $null
            ageMinutes = Get-PropertyValue -Object $_ -Name "ageMinutes" -Default $null
        }
    })
}

$statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
if (!(Test-Path -LiteralPath $statusScript -PathType Leaf)) {
    throw "Missing status script: $statusScript"
}

$statusResult = Invoke-CapturedCommand -FilePath "powershell" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $statusScript, "-Root", $Root) -WorkingDirectory $Root -TimeoutSeconds 120
if ($statusResult.timedOut) { throw "Status script timed out." }
if ($statusResult.exitCode -ne 0) { throw "Status script failed with exit code $($statusResult.exitCode): $($statusResult.combined)" }
if ([string]::IsNullOrWhiteSpace($statusResult.stdout)) { throw "Status script emitted no JSON." }

$status = $statusResult.stdout | ConvertFrom-Json -ErrorAction Stop
$counts = Get-PropertyValue -Object $status -Name "counts" -Default ([pscustomobject]@{})
$tasks = Get-PropertyValue -Object $status -Name "tasks" -Default ([pscustomobject]@{})
$slots = @(Get-PropertyValue -Object $status -Name "slots" -Default @())

$queue = @(Get-PropertyValue -Object $tasks -Name "queue" -Default @())
$active = @(Get-PropertyValue -Object $tasks -Name "active" -Default @())
$failed = @(Get-PropertyValue -Object $tasks -Name "failed" -Default @())

$helpers = @($slots | ForEach-Object {
    $attentionText = Get-SlotAttentionText -Slot $_
    [pscustomobject]@{
        role = ConvertTo-PublicRole -Slot $_
        status = ConvertTo-SafeText -Value ([string](Get-PropertyValue -Object $_ -Name "state" -Default "unknown"))
        category = ConvertTo-SafeCategory -Text $attentionText
        summary = ConvertTo-SafeText -Value ([string](Get-PropertyValue -Object $_ -Name "statusText" -Default ""))
        nextDecision = ConvertTo-SafeText -Value ([string](Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name "nextAction" -Default $null) -Name "action" -Default "Review when ready."))
    }
})

$needsAttention = @($helpers | Where-Object { $_.status -match "blocked|sleeping|stale|locked|needs" -or $_.category -ne "No action needed" } | Select-Object -First 8)

$dashboard = [pscustomobject]@{
    view = "product-manager"
    generatedAt = (Get-Date).ToString("o")
    headline = ConvertTo-SafeText -Value ([string](Get-PropertyValue -Object $status -Name "headline" -Default "Project status"))
    queueStatus = [pscustomobject]@{
        queued = Get-CountValue -Counts $counts -Name "queue"
        active = Get-CountValue -Counts $counts -Name "active"
        done = Get-CountValue -Counts $counts -Name "done"
        needsAttention = Get-CountValue -Counts $counts -Name "failed"
    }
    progress = [pscustomobject]@{
        activeWork = Get-SafeTaskSummary -Tasks $active
        upcomingWork = Get-SafeTaskSummary -Tasks $queue
    }
    attention = $needsAttention
    helpers = @($helpers | Select-Object -First 12)
    nextDecision = ConvertTo-SafeText -Value ([string](Get-PropertyValue -Object (Get-PropertyValue -Object $status -Name "nextAction" -Default $null) -Name "action" -Default "Review current queue and attention items."))
    redaction = [pscustomobject]@{
        mode = "pm-safe"
        hides = @("local paths", "task filenames", "raw agent names", "provider names", "worktree details", "raw command errors", "log tails")
    }
}

$jsonPath = Join-Path $OutputDir "product-manager-dashboard.json"
$htmlPath = Join-Path $OutputDir "product-manager-dashboard.html"
$dashboard | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

if (-not $JsonOnly) {
    $queueStatus = $dashboard.queueStatus
    $attentionItems = @($dashboard.attention)
    $helpersForHtml = @($dashboard.helpers)
    $activeWork = @($dashboard.progress.activeWork)
    $upcomingWork = @($dashboard.progress.upcomingWork)

    $attentionHtml = if ($attentionItems.Count -eq 0) {
        "<p>No product-level attention items.</p>"
    }
    else {
        ($attentionItems | ForEach-Object {
            "<li><strong>$(ConvertTo-HtmlText $_.category)</strong><br><span>$(ConvertTo-HtmlText $_.nextDecision)</span></li>"
        }) -join "`n"
    }

    $helpersHtml = if ($helpersForHtml.Count -eq 0) {
        "<p>No helper status available.</p>"
    }
    else {
        ($helpersForHtml | ForEach-Object {
"<li><strong>$(ConvertTo-HtmlText $_.role)</strong> - $(ConvertTo-HtmlText $_.status)<br><span>$(ConvertTo-HtmlText $_.category)</span></li>"
        }) -join "`n"
    }

    $activeHtml = if ($activeWork.Count -eq 0) { "<li>No active work reported.</li>" } else { ($activeWork | ForEach-Object { "<li>$(ConvertTo-HtmlText $_.title)</li>" }) -join "`n" }
    $upcomingHtml = if ($upcomingWork.Count -eq 0) { "<li>No queued work reported.</li>" } else { ($upcomingWork | ForEach-Object { "<li>$(ConvertTo-HtmlText $_.title)</li>" }) -join "`n" }

    $html = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Product Manager Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }
    .layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr); gap: 20px; }
    .card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .metric { background: #f1f5f9; border-radius: 10px; padding: 14px; }
    .metric strong { display: block; font-size: 28px; }
    h1, h2 { margin-top: 0; }
    li { margin: 0 0 12px 0; }
    ul { padding-left: 20px; }
    .muted { color: #64748b; font-size: 13px; }
    @media (max-width: 800px) { .layout, .metrics { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <h1>Product Manager Dashboard</h1>
  <p class="muted">Generated $(ConvertTo-HtmlText $dashboard.generatedAt). PM-safe view: implementation details are redacted.</p>
  <div class="layout">
    <main>
      <section class="card">
        <h2>Queue Status</h2>
        <div class="metrics">
          <div class="metric"><strong>$($queueStatus.queued)</strong>Queued</div>
          <div class="metric"><strong>$($queueStatus.active)</strong>Active</div>
          <div class="metric"><strong>$($queueStatus.done)</strong>Done</div>
          <div class="metric"><strong>$($queueStatus.needsAttention)</strong>Needs attention</div>
        </div>
      </section>
      <section class="card">
        <h2>Progress</h2>
        <h3>Active work</h3>
        <ul>$activeHtml</ul>
        <h3>Upcoming work</h3>
        <ul>$upcomingHtml</ul>
      </section>
      <section class="card">
        <h2>Helpers</h2>
        <ul>$helpersHtml</ul>
      </section>
    </main>
    <aside>
      <section class="card">
        <h2>What Needs Attention</h2>
        <ul>$attentionHtml</ul>
      </section>
      <section class="card">
        <h2>Next Decision</h2>
        <p>$(ConvertTo-HtmlText $dashboard.nextDecision)</p>
      </section>
    </aside>
  </div>
</body>
</html>
"@

    $html | Set-Content -LiteralPath $htmlPath -Encoding UTF8
}

$result = [pscustomobject]@{
    ok = $true
    issue = 217
    view = "product-manager"
    jsonPath = $jsonPath.Replace($Root, "").TrimStart("\")
    htmlPath = if ($JsonOnly) { $null } else { $htmlPath.Replace($Root, "").TrimStart("\") }
    generatedAt = $dashboard.generatedAt
}

$result | ConvertTo-Json -Depth 10
