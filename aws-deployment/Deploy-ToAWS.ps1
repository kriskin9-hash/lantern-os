# Deploy-ToAWS.ps1
# Deploys Lantern OS v1.0.0 to AWS ECS with CloudFormation

param(
    [string]$StackName = "lantern-os-stack",
    [string]$Region = "us-east-1",
    [string]$TemplateFile = "cloudformation-template.yaml",
    [string]$AppName = "lantern-os",
    [string]$Environment = "production",
    [string]$ContainerImage = "ghcr.io/alex-place/lantern-os:v1.0.0",
    [string]$DomainName = "lantern-os.app",
    [switch]$DryRun,
    [switch]$ValidateOnly
)

function Write-Step {
    param([string]$Message)
    Write-Host "▶ $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Check-Prerequisites {
    Write-Step "Checking prerequisites..."

    # Check AWS CLI
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
        Write-Error "AWS CLI not found. Install from: https://aws.amazon.com/cli/"
        exit 1
    }
    Write-Success "AWS CLI found"

    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity --region $Region 2>&1 | ConvertFrom-Json
        Write-Success "AWS credentials valid (Account: $($identity.Account))"
    } catch {
        Write-Error "AWS credentials not configured. Run: aws configure"
        exit 1
    }

    # Check CloudFormation template
    if (-not (Test-Path $TemplateFile)) {
        Write-Error "CloudFormation template not found: $TemplateFile"
        exit 1
    }
    Write-Success "CloudFormation template found"
}

function Validate-Template {
    Write-Step "Validating CloudFormation template..."

    try {
        $validation = aws cloudformation validate-template `
            --template-body "file://$TemplateFile" `
            --region $Region 2>&1 | ConvertFrom-Json

        Write-Success "Template validation passed"
        Write-Host "  Parameters: $($validation.Parameters.Count)"
        Write-Host "  Outputs: $($validation.OutputKeys.Count)"
    } catch {
        Write-Error "Template validation failed: $_"
        exit 1
    }
}

function Get-StackParameters {
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

    Write-Host "  AppName: $AppName"
    Write-Host "  Environment: $Environment"
    Write-Host "  Image: $ContainerImage"
    Write-Host "  Domain: $DomainName"

    return $parameters
}

function Create-Stack {
    param([array]$Parameters)

    Write-Step "Creating CloudFormation stack: $StackName"

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would execute:"
        Write-Host "    aws cloudformation create-stack ..."
        return
    }

    try {
        $stackOutput = aws cloudformation create-stack `
            --stack-name $StackName `
            --template-body "file://$TemplateFile" `
            --parameters $Parameters `
            --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
            --region $Region 2>&1 | ConvertFrom-Json

        Write-Success "Stack creation initiated"
        Write-Host "  Stack ID: $($stackOutput.StackId)"

        return $stackOutput.StackId
    } catch {
        Write-Error "Failed to create stack: $_"
        exit 1
    }
}

function Wait-For-Stack {
    param([string]$StackId)

    Write-Step "Waiting for stack creation (this may take 10-15 minutes)..."

    $maxWaitTime = 1800  # 30 minutes
    $checkInterval = 30  # seconds
    $elapsedTime = 0

    while ($elapsedTime -lt $maxWaitTime) {
        try {
            $stackStatus = aws cloudformation describe-stacks `
                --stack-name $StackId `
                --region $Region 2>&1 | ConvertFrom-Json

            $status = $stackStatus.Stacks[0].StackStatus

            if ($status -eq "CREATE_COMPLETE") {
                Write-Success "Stack created successfully"
                return $stackStatus.Stacks[0]
            } elseif ($status -like "*ROLLBACK*" -or $status -like "*FAILED*") {
                Write-Error "Stack creation failed with status: $status"
                # Get events
                Write-Step "Recent stack events:"
                $events = aws cloudformation describe-stack-events `
                    --stack-name $StackId `
                    --region $Region 2>&1 | ConvertFrom-Json

                $events.StackEvents | Select-Object -First 10 | ForEach-Object {
                    Write-Host "  [$($_.Timestamp)] $($_.ResourceStatus) - $($_.ResourceStatusReason)"
                }
                exit 1
            } else {
                $progress = [math]::Round(($elapsedTime / $maxWaitTime) * 100)
                Write-Host "  Status: $status ($progress%)" -ForegroundColor Yellow
            }
        } catch {
            Write-Error "Failed to check stack status: $_"
        }

        Start-Sleep -Seconds $checkInterval
        $elapsedTime += $checkInterval
    }

    Write-Error "Stack creation timeout after 30 minutes"
    exit 1
}

function Get-StackOutputs {
    param([string]$StackId)

    Write-Step "Retrieving stack outputs..."

    try {
        $stack = aws cloudformation describe-stacks `
            --stack-name $StackId `
            --region $Region 2>&1 | ConvertFrom-Json

        $outputs = @{}
        $stack.Stacks[0].Outputs | ForEach-Object {
            $outputs[$_.OutputKey] = $_.OutputValue
        }

        return $outputs
    } catch {
        Write-Error "Failed to retrieve stack outputs: $_"
        exit 1
    }
}

function Display-Results {
    param([hashtable]$Outputs)

    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host "🚀 LANTERN OS DEPLOYMENT COMPLETE" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host ""

    Write-Host "📋 Stack Outputs:" -ForegroundColor Cyan
    $Outputs.GetEnumerator() | ForEach-Object {
        Write-Host "  $($_.Key): $($_.Value)"
    }

    Write-Host ""
    Write-Host "🌐 Production URLs:" -ForegroundColor Cyan
    if ($Outputs.ContainsKey("APIEndpoint")) {
        Write-Host "  API:           $($Outputs.APIEndpoint)"
        Write-Host "  Dashboard:     $($Outputs.DashboardEndpoint)"
        Write-Host "  Browser STT:   $($Outputs.BrowserSTTEndpoint)"
        Write-Host "  Orchestrator:  $($Outputs.OrchestratorEndpoint)"
        Write-Host "  RAG Server:    $($Outputs.RAGEndpoint)"
    }

    Write-Host ""
    Write-Host "📍 Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Create Route53 hosted zone for $DomainName"
    Write-Host "  2. Add CNAME record: $DomainName → $($Outputs.LoadBalancerDNS)"
    Write-Host "  3. Wait 5-10 minutes for DNS propagation"
    Write-Host "  4. Update .env.production with permanent URLs"
    Write-Host "  5. Monitor CloudWatch: https://console.aws.amazon.com/cloudwatch"

    Write-Host ""
    Write-Host "📊 Monitoring:" -ForegroundColor Cyan
    Write-Host "  CloudWatch Logs: $($Outputs.LogGroupName)"
    Write-Host "  ECS Cluster:     $($Outputs.ClusterName)"
    Write-Host "  ECS Service:     $($Outputs.ServiceName)"

    Write-Host ""
    Write-Host "🔄 Manage Stack:" -ForegroundColor Cyan
    Write-Host "  View stack:     aws cloudformation describe-stacks --stack-name $StackName --region $Region"
    Write-Host "  Update stack:   aws cloudformation update-stack --stack-name $StackName --template-body file://cloudformation-template.yaml --region $Region"
    Write-Host "  Delete stack:   aws cloudformation delete-stack --stack-name $StackName --region $Region"
    Write-Host ""
}

# Main execution
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  LANTERN OS v1.0.0 — AWS Deployment                          ║" -ForegroundColor Magenta
Write-Host "║  CloudFormation Stack: $StackName" -ForegroundColor Magenta
Write-Host "║  Region: $Region" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

Check-Prerequisites
Validate-Template

if ($ValidateOnly) {
    Write-Success "Template validation successful. Exiting."
    exit 0
}

$parameters = Get-StackParameters

if (-not $DryRun) {
    $continue = Read-Host "Proceed with stack creation? (yes/no)"
    if ($continue -ne "yes") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

$stackId = Create-Stack -Parameters $parameters

if ($stackId -and -not $DryRun) {
    $stack = Wait-For-Stack -StackId $stackId
    $outputs = Get-StackOutputs -StackId $stackId
    Display-Results -Outputs $outputs
}

Write-Host ""
Write-Host "✅ Deployment process complete!" -ForegroundColor Green
Write-Host ""
