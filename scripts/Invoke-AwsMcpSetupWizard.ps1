param(
    [switch]$TestOnly,
    [switch]$DryRun,
    [switch]$SkipSafetyCheck
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    
    $logPath = "D:\tmp\lantern-os\data\automation\aws-mcp-setup.log"
    Add-Content -Path $logPath -Value "[$timestamp] [$Level] $Message" -ErrorAction SilentlyContinue
}

function Test-AwsCredentials {
    Write-Log "Checking AWS credentials..."
    
    $hasEnvVars = $env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY -and $env:AWS_DEFAULT_REGION
    $hasAwsCli = Get-Command "aws" -ErrorAction SilentlyContinue
    
    if ($hasAwsCli) {
        try {
            $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($identity) {
                return @{
                    valid = $true
                    account = $identity.Account
                    arn = $identity.Arn
                    method = "aws-cli"
                }
            }
        }
        catch {
            Write-Log "AWS CLI credentials check failed: $_" "WARN"
        }
    }
    
    if ($hasEnvVars) {
        return @{
            valid = $true
            method = "environment-variables"
            maskedKey = ($env:AWS_ACCESS_KEY_ID.Substring(0, 4) + "****")
            region = $env:AWS_DEFAULT_REGION
        }
    }
    
    return @{
        valid = $false
        reason = "No AWS credentials found"
        envVarsConfigured = $hasEnvVars
        cliInstalled = ($hasAwsCli -ne $null)
    }
}

function Test-WindsurfAwsToolkit {
    Write-Log "Checking AWS Toolkit in Windsurf..."
    
    # Check common Windsurf extension paths
    $extensionPaths = @(
        "$env:USERPROFILE\.windsurf\extensions\amazonwebservices.aws-toolkit-vscode*",
        "$env:USERPROFILE\.vscode\extensions\amazonwebservices.aws-toolkit-vscode*"
    )
    
    $found = $false
    foreach ($path in $extensionPaths) {
        if (Test-Path $path) {
            $found = $true
            break
        }
    }
    
    return @{
        installed = $found
        pathsChecked = $extensionPaths.Count
        note = if (-not $found) { "Install from Windsurf Extensions panel" } else { "Found" }
    }
}

function Test-McpConfiguration {
    Write-Log "Checking Windsurf MCP configuration..."
    
    # Common Windsurf config locations
    $configPaths = @(
        "$env:USERPROFILE\.windsurf\mcp_config.json",
        "$env:APPDATA\Windsurf\mcp_config.json"
    )
    
    $foundConfig = $null
    foreach ($path in $configPaths) {
        if (Test-Path $path) {
            $foundConfig = $path
            break
        }
    }
    
    if ($foundConfig) {
        try {
            $config = Get-Content $foundConfig -Raw | ConvertFrom-Json
            $hasAws = $config.mcpServers.PSObject.Properties.Name -contains "aws-cli" -or 
                      $config.mcpServers.PSObject.Properties.Name -contains "aws"
            
            return @{
                configFound = $true
                configPath = $foundConfig
                hasAwsMcp = $hasAws
                serversConfigured = ($config.mcpServers.PSObject.Properties.Name).Count
            }
        }
        catch {
            return @{
                configFound = $true
                configPath = $foundConfig
                error = "Failed to parse: $_"
            }
        }
    }
    
    return @{
        configFound = $false
        checkedPaths = $configPaths
        nextAction = "Create mcp_config.json in Windsurf settings"
    }
}

function Get-SetupStatus {
    $awsCreds = Test-AwsCredentials
    $awsToolkit = Test-WindsurfAwsToolkit
    $mcpConfig = Test-McpConfiguration
    
    $readyForCanary = $awsCreds.valid -and $mcpConfig.configFound -and $mcpConfig.hasAwsMcp
    
    return @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        credentials = $awsCreds
        toolkit = $awsToolkit
        mcpConfig = $mcpConfig
        readyForCanary = $readyForCanary
        overallStatus = if ($readyForCanary) { "ready-for-canary" } else { "setup-incomplete" }
        nextActions = @(
            if (-not $awsCreds.valid) { "Configure AWS credentials (env vars or AWS CLI)" }
            if (-not $mcpConfig.configFound) { "Create Windsurf MCP config file" }
            if ($mcpConfig.configFound -and -not $mcpConfig.hasAwsMcp) { "Add AWS MCP server to config" }
            if ($readyForCanary) { "Run: .\scripts\Invoke-McpCanaryTest.ps1 -Provider aws" }
        ) | Where-Object { $_ -ne $null }
    }
}

function Invoke-AwsMcpSetupWizard {
    Write-Log "=== AWS MCP Setup Wizard ==="
    
    if ($DryRun) {
        Write-Log "DRY RUN MODE - No changes will be made"
    }
    
    # Safety check
    if (-not $SkipSafetyCheck) {
        Write-Log "Running safety checks..."
        $hooksActive = Test-Path "D:\tmp\lantern-os\.windsurf\hooks.json"
        if (-not $hooksActive) {
            Write-Log "WARNING: Windsurf safety hooks not detected" "WARN"
            Write-Log "Recommended: Ensure .windsurf/hooks.json is configured" "WARN"
        }
    }
    
    # Get current status
    $status = Get-SetupStatus
    
    Write-Log ""
    Write-Log "=== AWS Credential Status ==="
    Write-Log "Valid: $($status.credentials.valid)"
    if ($status.credentials.valid) {
        Write-Log "Method: $($status.credentials.method)"
        if ($status.credentials.account) {
            Write-Log "Account: $($status.credentials.account)"
        }
    }
    else {
        Write-Log "Reason: $($status.credentials.reason)" "WARN"
    }
    
    Write-Log ""
    Write-Log "=== AWS Toolkit Status ==="
    Write-Log "Installed: $($status.toolkit.installed)"
    if (-not $status.toolkit.installed) {
        Write-Log "Note: $($status.toolkit.note)"
    }
    
    Write-Log ""
    Write-Log "=== MCP Configuration Status ==="
    Write-Log "Config Found: $($status.mcpConfig.configFound)"
    if ($status.mcpConfig.configFound) {
        Write-Log "Path: $($status.mcpConfig.configPath)"
        Write-Log "AWS MCP Configured: $($status.mcpConfig.hasAwsMcp)"
        Write-Log "Total Servers: $($status.mcpConfig.serversConfigured)"
    }
    else {
        Write-Log "Checked: $($status.mcpConfig.checkedPaths -join ', ')"
    }
    
    Write-Log ""
    Write-Log "=== Overall Status ==="
    Write-Log "Status: $($status.overallStatus)"
    
    Write-Log ""
    Write-Log "=== Next Actions ==="
    foreach ($action in $status.nextActions) {
        Write-Log "  - $action"
    }
    
    # Save results
    $outputPath = "D:\tmp\lantern-os\data\automation\aws-mcp-setup-status.json"
    if (-not $DryRun) {
        $status | ConvertTo-Json -Depth 10 | Set-Content $outputPath
        Write-Log ""
        Write-Log "Status saved to: $outputPath"
    }
    
    # Test mode - run validation if requested
    if ($TestOnly -and $status.readyForCanary) {
        Write-Log ""
        Write-Log "Test mode active - would run canary test now"
        Write-Log "Run manually: .\scripts\Invoke-McpCanaryTest.ps1 -Provider aws"
    }
    
    return $status
}

# Main
Invoke-AwsMcpSetupWizard
