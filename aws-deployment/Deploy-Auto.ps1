# Deploy-Auto.ps1
# Non-interactive AWS deployment script (no prompts)

param(
    [string]$StackName = "lantern-os-stack",
    [string]$Region = "us-east-1",
    [string]$TemplateFile = "cloudformation-template.yaml",
    [string]$AppName = "lantern-os",
    [string]$Environment = "production",
    [string]$ContainerImage = "ghcr.io/alex-place/lantern-os:v1.0.0",
    [string]$DomainName = "lantern-os.app"
)

$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Message); Write-Host "▶ $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message); Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message); Write-Host "ℹ️ $Message" -ForegroundColor Yellow }

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  LANTERN OS v1.0.0 — AWS Production Deployment               ║" -ForegroundColor Magenta
Write-Host "║  Auto-Mode (Non-Interactive)                                 ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

Write-Info "Configuration:"
Write-Host "  Stack Name:    $StackName"
Write-Host "  Region:        $Region"
Write-Host "  Domain:        $DomainName"
Write-Host "  Container:     $ContainerImage"
Write-Host ""

# Check AWS CLI
Write-Step "Checking AWS CLI..."
try {
    $version = aws --version 2>&1
    Write-Success "AWS CLI: $version"
} catch {
    Write-Error "AWS CLI not found"
    exit 1
}

# Check credentials
Write-Step "Verifying AWS credentials..."
try {
    $identity = aws sts get-caller-identity --region $Region 2>&1 | ConvertFrom-Json
    Write-Success "AWS Account: $($identity.Account)"
    Write-Host "  ARN: $($identity.Arn)"
} catch {
    Write-Error "AWS credentials invalid or not configured"
    Write-Host "  Run: aws configure"
    exit 1
}

# Validate template
Write-Step "Validating CloudFormation template..."
if (-not (Test-Path $TemplateFile)) {
    Write-Error "Template not found: $TemplateFile"
    exit 1
}

try {
    $validation = aws cloudformation validate-template `
        --template-body "file://$TemplateFile" `
        --region $Region 2>&1 | ConvertFrom-Json
    Write-Success "Template validation passed"
} catch {
    Write-Error "Template validation failed: $_"
    exit 1
}

# Check if stack exists
Write-Step "Checking if stack already exists..."
try {
    $existing = aws cloudformation describe-stacks `
        --stack-name $StackName `
        --region $Region 2>&1 | ConvertFrom-Json
    Write-Info "Stack '$StackName' already exists (Status: $($existing.Stacks[0].StackStatus))"
    Write-Host "  Will update existing stack instead of creating new one"
} catch {
    Write-Info "Stack '$StackName' does not exist yet (will create)"
}

# Prepare parameters
Write-Step "Preparing stack parameters..."
$parameters = @(
    "ParameterKey=AppName,ParameterValue=$AppName"
    "ParameterKey=Environment,ParameterValue=$Environment"
    "ParameterKey=ContainerImage,ParameterValue=$ContainerImage"
    "ParameterKey=DomainName,ParameterValue=$DomainName"
    "ParameterKey=TaskCpu,ParameterValue=1024"
    "ParameterKey=TaskMemory,ParameterValue=2048"
    "ParameterKey=DesiredCount,ParameterValue=2"
)
Write-Success "Parameters prepared"

# Create or update stack
Write-Step "Creating CloudFormation stack (this takes 10-15 minutes)..."
Write-Host ""

try {
    $stackOutput = aws cloudformation create-stack `
        --stack-name $StackName `
        --template-body "file://$TemplateFile" `
        --parameters $parameters `
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
        --region $Region 2>&1 | ConvertFrom-Json

    $stackId = $stackOutput.StackId
    Write-Success "Stack creation initiated"
    Write-Host "  ID: $stackId"
} catch {
    if ($_ -match "AlreadyExistsException") {
        Write-Info "Stack already exists, updating..."
        try {
            $stackOutput = aws cloudformation update-stack `
                --stack-name $StackName `
                --template-body "file://$TemplateFile" `
                --parameters $parameters `
                --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
                --region $Region 2>&1 | ConvertFrom-Json
            $stackId = $stackOutput.StackId
            Write-Success "Stack update initiated"
        } catch {
            Write-Error "Stack update failed: $_"
            exit 1
        }
    } else {
        Write-Error "Stack creation failed: $_"
        exit 1
    }
}

# Wait for stack completion
Write-Step "Waiting for stack to be ready (monitoring progress)..."
$maxWait = 1800  # 30 minutes
$checkInterval = 30
$elapsed = 0
$lastStatus = ""

while ($elapsed -lt $maxWait) {
    try {
        $stack = aws cloudformation describe-stacks `
            --stack-name $stackId `
            --region $Region 2>&1 | ConvertFrom-Json

        $status = $stack.Stacks[0].StackStatus

        if ($status -ne $lastStatus) {
            Write-Info "Status: $status"
            $lastStatus = $status
        }

        if ($status -eq "CREATE_COMPLETE" -or $status -eq "UPDATE_COMPLETE") {
            Write-Success "Stack ready!"
            break
        } elseif ($status -like "*FAILED*" -or $status -like "*ROLLBACK*") {
            Write-Error "Stack creation failed with status: $status"

            # Show events
            Write-Step "Recent stack events:"
            $events = aws cloudformation describe-stack-events `
                --stack-name $stackId `
                --region $Region 2>&1 | ConvertFrom-Json

            $events.StackEvents | Select-Object -First 5 | ForEach-Object {
                Write-Host "  [$($_.ResourceStatus)] $($_.LogicalResourceId)"
                if ($_.ResourceStatusReason) {
                    Write-Host "    Reason: $($_.ResourceStatusReason)"
                }
            }
            exit 1
        }

        $percent = [math]::Min(99, [math]::Round(($elapsed / $maxWait) * 100))
        Write-Host "  Progress: $percent% ($elapsed/$maxWait seconds)" -ForegroundColor DarkGray
    } catch {
        Write-Host "  (Checking stack status...)" -ForegroundColor DarkGray
    }

    Start-Sleep -Seconds $checkInterval
    $elapsed += $checkInterval
}

if ($elapsed -ge $maxWait) {
    Write-Error "Stack creation timeout"
    exit 1
}

# Retrieve outputs
Write-Step "Retrieving stack outputs..."
try {
    $stack = aws cloudformation describe-stacks `
        --stack-name $stackId `
        --region $Region 2>&1 | ConvertFrom-Json

    $outputs = @{}
    $stack.Stacks[0].Outputs | ForEach-Object {
        $outputs[$_.OutputKey] = $_.OutputValue
    }

    Write-Success "Stack outputs retrieved"
} catch {
    Write-Error "Failed to get outputs: $_"
    exit 1
}

# Display results
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "🚀 LANTERN OS DEPLOYMENT SUCCESSFUL" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""

Write-Host "📋 Stack Outputs:" -ForegroundColor Cyan
$outputs.GetEnumerator() | ForEach-Object {
    Write-Host "  $($_.Key): $($_.Value)"
}

Write-Host ""
Write-Host "🌐 Production URLs:" -ForegroundColor Cyan
Write-Host "  API:           $($outputs.APIEndpoint)"
Write-Host "  Dashboard:     $($outputs.DashboardEndpoint)"
Write-Host "  Browser STT:   $($outputs.BrowserSTTEndpoint)"
Write-Host "  Orchestrator:  $($outputs.OrchestratorEndpoint)"
Write-Host "  RAG Server:    $($outputs.RAGEndpoint)"

Write-Host ""
Write-Host "🔗 Load Balancer DNS:" -ForegroundColor Cyan
Write-Host "  $($outputs.LoadBalancerDNS)"

Write-Host ""
Write-Host "📍 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Add DNS record: CNAME lantern-os.app → $($outputs.LoadBalancerDNS)"
Write-Host "  2. Wait 5-10 minutes for DNS propagation"
Write-Host "  3. Test: curl https://lantern-os.app/health"
Write-Host "  4. Update .env.production with permanent URLs"
Write-Host "  5. Monitor logs: aws logs tail /ecs/lantern-os --follow"

Write-Host ""
Write-Host "📊 Monitoring & Management:" -ForegroundColor Cyan
Write-Host "  CloudWatch Logs: $($outputs.LogGroupName)"
Write-Host "  ECS Cluster:     $($outputs.ClusterName)"
Write-Host "  ECS Service:     $($outputs.ServiceName)"

Write-Host ""
Write-Host "🔐 SSL/TLS Setup:" -ForegroundColor Cyan
Write-Host "  1. Create ACM certificate for $DomainName"
Write-Host "  2. Update ALB listener to use HTTPS"
Write-Host "  3. Redirect HTTP → HTTPS"

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "✅ Lantern OS is now running on AWS!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""

# Save outputs to file
$outputsFile = "deployment-outputs.json"
$outputs | ConvertTo-Json | Set-Content -Path $outputsFile
Write-Success "Outputs saved to: $outputsFile"

Write-Host ""
Write-Host "✨ Deployment complete! Your infrastructure is ready for production." -ForegroundColor Green
Write-Host ""
