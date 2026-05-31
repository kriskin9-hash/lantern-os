param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [switch]$DryRun,
    [switch]$Report
)

$ErrorActionPreference = "Stop"

# --- Mookman Report 4 style rules ---
# Each rule: Pattern (regex), Replacement (or $null for flag-only), Severity, Reason
$rules = @(
    # Metaphorical phase names
    @{ Pattern = 'Movie 1[^a-zA-Z]'; Replace = 'Phase 1 —'; Severity = 'warn'; Reason = 'Metaphorical phase name; use plain phase label' }
    @{ Pattern = 'Movie 2[^a-zA-Z]'; Replace = 'Phase 2 —'; Severity = 'warn'; Reason = 'Metaphorical phase name; use plain phase label' }
    @{ Pattern = 'Movie 3[^a-zA-Z]'; Replace = 'Phase 3 —'; Severity = 'warn'; Reason = 'Metaphorical phase name; use plain phase label' }
    @{ Pattern = 'garage prototype'; Replace = 'local prototype'; Severity = 'warn'; Reason = 'Metaphor; use descriptive technical term' }
    @{ Pattern = 'garage-prototype'; Replace = 'local-prototype'; Severity = 'warn'; Reason = 'Metaphor; use descriptive technical term' }

    # Overclaim language
    @{ Pattern = 'perfect(?![ly])'; Replace = $null; Severity = 'error'; Reason = 'Overclaim — "perfect" unless validation passed' }
    @{ Pattern = '\blive\b(?! demo| test| data| stream| run| state| check)'; Replace = $null; Severity = 'warn'; Reason = 'Unverified live-state claim' }
    @{ Pattern = '\breadily\b'; Replace = $null; Severity = 'warn'; Reason = 'Vague claim language' }
    @{ Pattern = '\bseamlessly\b'; Replace = $null; Severity = 'warn'; Reason = 'Vague claim language' }
    @{ Pattern = '\bpowerful\b'; Replace = $null; Severity = 'info'; Reason = 'Vague — prefer specific capability description' }
    @{ Pattern = '\brobust\b'; Replace = $null; Severity = 'info'; Reason = 'Vague — prefer specific evidence' }
    @{ Pattern = '\bcutting.edge\b'; Replace = $null; Severity = 'warn'; Reason = 'Marketing language — remove or cite evidence' }
    @{ Pattern = '\bworld.class\b'; Replace = $null; Severity = 'warn'; Reason = 'Overclaim — no validation path cited' }
    @{ Pattern = '\brevolutionary\b'; Replace = $null; Severity = 'warn'; Reason = 'Overclaim — cite evidence or remove' }
    @{ Pattern = '\bgroundbreaking\b'; Replace = $null; Severity = 'warn'; Reason = 'Overclaim — cite evidence or remove' }

    # Path/command spam before explanation
    @{ Pattern = '^`[A-Z]:\\'; Replace = $null; Severity = 'info'; Reason = 'Raw path before explanation — move to appendix' }

    # Fake active state
    @{ Pattern = '\bis (running|active|live|online)\b'; Replace = $null; Severity = 'warn'; Reason = 'Unverified active state claim' }

    # Structural: missing Simple Answer
    @{ Pattern = $null; Replace = $null; Severity = 'structure'; Reason = 'Check for ## Simple Answer section' }
)

$filePath = Resolve-Path $Path -ErrorAction SilentlyContinue
if (-not $filePath) {
    Write-Error "File not found: $Path"
    exit 1
}

$content   = Get-Content -LiteralPath $filePath -Raw -Encoding UTF8
$lines     = $content -split "`n"
$findings  = [System.Collections.Generic.List[object]]::new()
$modified  = $content

# Structural check: Simple Answer
if ($content -notmatch '## Simple Answer') {
    $findings.Add([pscustomobject]@{
        Line = 0; Severity = 'warn'
        Rule = 'Missing ## Simple Answer section (Mookman 4 shape requires it)'
        Text = ''
    })
}

# Line-by-line rule scan
for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    foreach ($rule in $rules) {
        if (-not $rule.Pattern) { continue }
        if ($line -match $rule.Pattern) {
            $findings.Add([pscustomobject]@{
                Line     = $i + 1
                Severity = $rule.Severity
                Rule     = $rule.Reason
                Text     = $line.Trim()
            })
            if ($rule.Replace -ne $null -and -not $DryRun -and -not $Report) {
                $modified = $modified -replace $rule.Pattern, $rule.Replace
            }
        }
    }
}

# --- Output ---
$errors   = @($findings | Where-Object { $_.Severity -eq 'error' })
$warnings = @($findings | Where-Object { $_.Severity -eq 'warn' })
$infos    = @($findings | Where-Object { $_.Severity -eq 'info' })

Write-Host "`n=== Style Convergence: $(Split-Path $filePath -Leaf) ===" -ForegroundColor Cyan
Write-Host "Errors  : $($errors.Count)" -ForegroundColor $(if ($errors.Count -gt 0) { 'Red' } else { 'Green' })
Write-Host "Warnings: $($warnings.Count)" -ForegroundColor $(if ($warnings.Count -gt 0) { 'Yellow' } else { 'Green' })
Write-Host "Info    : $($infos.Count)" -ForegroundColor Gray

foreach ($f in $findings) {
    $color = switch ($f.Severity) {
        'error' { 'Red' }
        'warn'  { 'Yellow' }
        default { 'Gray' }
    }
    $prefix = switch ($f.Severity) {
        'error' { '[ERROR]' }
        'warn'  { '[ WARN]' }
        default { '[ INFO]' }
    }
    $loc = if ($f.Line -gt 0) { "L$($f.Line)" } else { "struct" }
    Write-Host ("  $prefix $loc  $($f.Rule)") -ForegroundColor $color
    if ($f.Text) {
        Write-Host ("           > $($f.Text.Substring(0, [Math]::Min(90, $f.Text.Length)))") -ForegroundColor DarkGray
    }
}

if ($Report) {
    Write-Host "`n[REPORT MODE] No changes written." -ForegroundColor Yellow
    exit 0
}

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would apply auto-fixes for $($findings | Where-Object { $_.Replace -ne $null } | Measure-Object | Select-Object -ExpandProperty Count) rules." -ForegroundColor Yellow
    exit 0
}

if ($modified -ne $content) {
    Set-Content -LiteralPath $filePath -Value $modified -Encoding UTF8 -NoNewline
    Write-Host "`nAuto-fixes applied and saved." -ForegroundColor Green
} else {
    Write-Host "`nNo auto-fixable patterns found." -ForegroundColor Green
}

exit $(if ($errors.Count -gt 0) { 1 } else { 0 })
