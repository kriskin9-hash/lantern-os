# Quick-Deploy.ps1
# One-command deployment of Lantern OS to AWS

param(
    [string]$StackName = "lantern-os-stack",
    [string]$Region = "us-east-1",
    [string]$DomainName = "lantern-os.app",
    [switch]$SkipDNS
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  LANTERN OS — Quick Deploy to AWS                            ║" -ForegroundColor Magenta
Write-Host "║  This will deploy your production infrastructure in ~35min   ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

Write-Host "📋 Deployment Configuration:" -ForegroundColor Cyan
Write-Host "  Stack Name: $StackName"
Write-Host "  Region: $Region"
Write-Host "  Domain: $DomainName"
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "Ready to deploy? This will create AWS resources. (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "▶ Step 1: Validating prerequisites..." -ForegroundColor Cyan

try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    Write-Host "✅ AWS credentials valid (Account: $($identity.Account))" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "▶ Step 2: Deploying CloudFormation stack..." -ForegroundColor Cyan

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$templateFile = Join-Path $scriptPath "cloudformation-template.yaml"

& "$scriptPath\Deploy-ToAWS.ps1" `
    -StackName $StackName `
    -Region $Region `
    -TemplateFile $templateFile `
    -DomainName $DomainName

Write-Host ""

if (-not $SkipDNS) {
    $setupDNS = Read-Host "Configure DNS with Route53? (yes/no)"
    if ($setupDNS -eq "yes") {
        Write-Host ""
        Write-Host "▶ Step 3: Setting up Route53 DNS..." -ForegroundColor Cyan
        Write-Host ""
        & "$scriptPath\Setup-DNS.ps1" -DomainName $DomainName -Region $Region
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""

Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Verify DNS propagation:"
Write-Host "     nslookup $DomainName"
Write-Host ""
Write-Host "  2. Test your services:"
Write-Host "     curl https://$DomainName/health"
Write-Host ""
Write-Host "  3. Monitor logs:"
Write-Host "     aws logs tail /ecs/lantern-os --follow"
Write-Host ""
Write-Host "  4. View dashboard:"
Write-Host "     https://$DomainName:4177"
Write-Host ""
Write-Host "  5. Update your agent slots with permanent URLs:"
Write-Host "     Edit: .claude/launch.json"
Write-Host "     Set all LANTERN_* URLs to https://$DomainName/..."
Write-Host ""

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "  Complete guide: ./AWS-DEPLOYMENT-GUIDE.md"
Write-Host "  CloudFormation: https://console.aws.amazon.com/cloudformation"
Write-Host "  ECS Dashboard:  https://console.aws.amazon.com/ecs"
Write-Host "  CloudWatch:     https://console.aws.amazon.com/cloudwatch"
Write-Host ""

Write-Host "✅ Your Lantern OS is now deployed to production!" -ForegroundColor Green
Write-Host ""
