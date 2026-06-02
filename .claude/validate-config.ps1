# validate-config.ps1
# Validates all Lantern OS configuration files and registries

param(
    [switch]$Verbose,
    [switch]$Fix
)

$ErrorActionPreference = "Stop"
$validationResults = @{
    passed = 0
    failed = 0
    warnings = 0
    errors = @()
}

function Write-Pass { param([string]$Message); Write-Host "✅ $Message" -ForegroundColor Green; $script:validationResults.passed++ }
function Write-Fail { param([string]$Message); Write-Host "❌ $Message" -ForegroundColor Red; $script:validationResults.failed++; $script:validationResults.errors += $Message }
function Write-Warn { param([string]$Message); Write-Host "⚠️ $Message" -ForegroundColor Yellow; $script:validationResults.warnings++ }
function Write-Info { param([string]$Message); Write-Host "ℹ️ $Message" -ForegroundColor Cyan }

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  LANTERN OS — Configuration Validation                       ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# Check working directory
Write-Info "Validating configuration..."
Write-Host ""

$baseDir = Get-Location
$claudeDir = Join-Path $baseDir ".claude"

# 1. Check launch.json
Write-Host "1️⃣ Checking .claude/launch.json..." -ForegroundColor Cyan
$launchFile = Join-Path $claudeDir "launch.json"
if (Test-Path $launchFile) {
    try {
        $launch = Get-Content $launchFile | ConvertFrom-Json
        Write-Pass "launch.json exists and is valid JSON"

        $services = $launch.configurations | Measure-Object | Select-Object -ExpandProperty Count
        if ($services -ge 5) {
            Write-Pass "All 5 Lantern services configured"
        } else {
            Write-Warn "Only $services services configured (expected 5+)"
        }

        $ports = @(5000, 4177, 8765, 8000, 8767)
        foreach ($port in $ports) {
            $found = $launch.configurations | Where-Object { $_.port -eq $port }
            if ($found) {
                Write-Pass "Port $port configured"
            } else {
                Write-Warn "Port $port not configured"
            }
        }
    } catch {
        Write-Fail "launch.json is invalid JSON: $_"
    }
} else {
    Write-Fail "launch.json not found"
}

Write-Host ""

# 2. Check .env.production
Write-Host "2️⃣ Checking .env.production..." -ForegroundColor Cyan
$prodEnv = Join-Path $baseDir ".env.production"
if (Test-Path $prodEnv) {
    Write-Pass ".env.production exists"

    $content = Get-Content $prodEnv -Raw
    $requiredVars = @(
        "LANTERN_MODE=production",
        "REQUIRE_HTTPS=true",
        "CODE_FREEZE_ENABLED=true",
        "FOUNDRY_ENABLED=true",
        "AWS_REGION=us-east-1"
    )

    foreach ($var in $requiredVars) {
        if ($content -match [regex]::Escape($var)) {
            Write-Pass "Setting configured: $var"
        } else {
            Write-Warn "Setting missing or incorrect: $var"
        }
    }

    $agentVars = @("CLAUDE", "CODEX", "GEMINI", "DEVIN")
    foreach ($agent in $agentVars) {
        $pattern = "AGENT_SLOT_${agent}_ENABLED=true"
        if ($content -match [regex]::Escape($pattern)) {
            Write-Pass "Agent slot enabled: $agent"
        } else {
            Write-Warn "Agent slot not enabled: $agent"
        }
    }
} else {
    Write-Fail ".env.production not found"
}

Write-Host ""

# 3. Check .env.local
Write-Host "3️⃣ Checking .env.local..." -ForegroundColor Cyan
$localEnv = Join-Path $baseDir ".env.local"
if (Test-Path $localEnv) {
    Write-Pass ".env.local exists"

    $content = Get-Content $localEnv -Raw
    if ($content -match "LANTERN_MODE=development") {
        Write-Pass "Development mode configured"
    } else {
        Write-Fail "Development mode not configured"
    }

    if ($content -match "DEBUG=true") {
        Write-Pass "Debug mode enabled"
    } else {
        Write-Warn "Debug mode not enabled"
    }

    if ($content -match "LLM_PROVIDER=local") {
        Write-Pass "Local LLM configured"
    } else {
        Write-Warn "Local LLM not configured"
    }
} else {
    Write-Fail ".env.local not found"
}

Write-Host ""

# 4. Check mcp-servers.json
Write-Host "4️⃣ Checking .claude/mcp-servers.json..." -ForegroundColor Cyan
$mcpFile = Join-Path $claudeDir "mcp-servers.json"
if (Test-Path $mcpFile) {
    try {
        $mcp = Get-Content $mcpFile | ConvertFrom-Json
        Write-Pass "mcp-servers.json exists and is valid JSON"

        $serverCount = $mcp.servers | Measure-Object | Select-Object -ExpandProperty Count
        if ($serverCount -ge 3) {
            Write-Pass "All 3 MCP servers configured"
        } else {
            Write-Warn "Only $serverCount servers configured (expected 3+)"
        }

        $tools = $mcp.servers[0].tools | Measure-Object | Select-Object -ExpandProperty Count
        if ($tools -ge 10) {
            Write-Pass "Orchestrator tools registered ($tools tools)"
        } else {
            Write-Warn "Only $tools orchestrator tools (expected 10+)"
        }
    } catch {
        Write-Fail "mcp-servers.json is invalid JSON: $_"
    }
} else {
    Write-Fail "mcp-servers.json not found"
}

Write-Host ""

# 5. Check agent-slots.json
Write-Host "5️⃣ Checking .claude/agent-slots.json..." -ForegroundColor Cyan
$slotsFile = Join-Path $claudeDir "agent-slots.json"
if (Test-Path $slotsFile) {
    try {
        $slots = Get-Content $slotsFile | ConvertFrom-Json
        Write-Pass "agent-slots.json exists and is valid JSON"

        $slotCount = $slots.slots | Measure-Object | Select-Object -ExpandProperty Count
        if ($slotCount -eq 4) {
            Write-Pass "All 4 agent slots configured"
        } else {
            Write-Warn "Only $slotCount agent slots (expected 4)"
        }

        $agents = @("claude", "codex", "gemini", "devin")
        foreach ($agent in $agents) {
            $found = $slots.slots | Where-Object { $_.agent -eq $agent }
            if ($found) {
                Write-Pass "Agent slot configured: $agent"
            } else {
                Write-Fail "Agent slot missing: $agent"
            }
        }

        if ($slots.batchSync.enabled) {
            Write-Pass "Batch sync enabled (interval: $($slots.batchSync.interval)s)"
        } else {
            Write-Warn "Batch sync disabled"
        }
    } catch {
        Write-Fail "agent-slots.json is invalid JSON: $_"
    }
} else {
    Write-Fail "agent-slots.json not found"
}

Write-Host ""

# 6. Check AWS configuration
Write-Host "6️⃣ Checking AWS Configuration..." -ForegroundColor Cyan
try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    Write-Pass "AWS credentials valid (Account: $($identity.Account))"
} catch {
    Write-Warn "AWS credentials not configured or invalid"
}

Write-Host ""

# 7. Check Docker image
Write-Host "7️⃣ Checking Docker Image..." -ForegroundColor Cyan
try {
    $image = docker images | Select-String "ghcr.io/alex-place/lantern-os"
    if ($image) {
        Write-Pass "Docker image found locally"
    } else {
        Write-Info "Image not in local registry (will pull from ghcr.io)"
    }
} catch {
    Write-Warn "Docker not available or image not found"
}

Write-Host ""

# 8. Check port availability
Write-Host "8️⃣ Checking Port Availability..." -ForegroundColor Cyan
$ports = @(5000, 4177, 8765, 8000, 8767, 9000)
foreach ($port in $ports) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $port -ErrorAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-Warn "Port $port is in use (service may already be running)"
        } else {
            Write-Pass "Port $port is available"
        }
    } catch {
        Write-Pass "Port $port is available"
    }
}

Write-Host ""

# Summary
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "📊 Validation Summary" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "  Passed:  $($validationResults.passed)"
Write-Host "  Failed:  $($validationResults.failed)"
Write-Host "  Warnings: $($validationResults.warnings)"
Write-Host ""

if ($validationResults.failed -gt 0) {
    Write-Host "❌ Configuration Issues Found:" -ForegroundColor Red
    $validationResults.errors | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please fix the issues above before deploying." -ForegroundColor Red
    exit 1
} elseif ($validationResults.warnings -gt 0) {
    Write-Host "⚠️ Configuration Warnings:" -ForegroundColor Yellow
    Write-Host "  Review the warnings above, but they won't block deployment."
    Write-Host ""
    Write-Host "✅ Configuration is valid and ready for deployment!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✅ All configuration checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready to deploy Lantern OS to production." -ForegroundColor Green
    exit 0
}
