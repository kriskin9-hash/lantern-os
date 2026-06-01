param(
    [string]$Environment = 'production',
    [string]$AwsRegion = 'us-east-1',
    [string]$RepositoryUri = '',
    [string]$ImageTag = 'latest'
)

$ErrorActionPreference = "Stop"

Write-Host "Deploying Lantern OS to AWS ECS" -ForegroundColor Cyan

# Step 1: Build Docker image
Write-Host "`n[1/5] Building Docker image..." -ForegroundColor Yellow
docker build -f Dockerfile.unified -t lantern-os:$ImageTag .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed"
    exit 1
}

# Step 2: Get AWS Account ID
Write-Host "`n[2/5] Getting AWS credentials..." -ForegroundColor Yellow
$AwsAccountId = aws sts get-caller-identity --query Account --output text
Write-Host "AWS Account: $AwsAccountId"

# Step 3: Create ECR repository (if not exists)
Write-Host "`n[3/5] Setting up ECR repository..." -ForegroundColor Yellow
$RepositoryUri = "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com/lantern-os"

try {
    aws ecr describe-repositories --repository-names lantern-os --region $AwsRegion | Out-Null
    Write-Host "Repository exists: $RepositoryUri"
} catch {
    Write-Host "Creating new repository..."
    aws ecr create-repository --repository-name lantern-os --region $AwsRegion
}

# Step 4: Login to ECR and push image
Write-Host "`n[4/5] Pushing Docker image to ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin $RepositoryUri
docker tag lantern-os:$ImageTag $RepositoryUri`:$ImageTag
docker push $RepositoryUri`:$ImageTag

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker push failed"
    exit 1
}

Write-Host "[OK] Image pushed: $RepositoryUri`:$ImageTag" -ForegroundColor Green

# Step 5: Deploy CloudFormation stack
Write-Host "`n[5/5] Deploying CloudFormation stack..." -ForegroundColor Yellow

$StackName = "lantern-os-stack"
$TemplateFile = "aws-deployment/cloudformation-template.yaml"

aws cloudformation deploy `
    --template-file $TemplateFile `
    --stack-name $StackName `
    --parameter-overrides `
        Environment=$Environment `
        ContainerImage=$RepositoryUri`:$ImageTag `
        DesiredCount=2 `
    --capabilities CAPABILITY_IAM `
    --region $AwsRegion `
    --no-fail-on-empty-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Stack deployment successful!" -ForegroundColor Green

    # Get outputs
    $Outputs = aws cloudformation describe-stacks `
        --stack-name $StackName `
        --region $AwsRegion `
        --query 'Stacks[0].Outputs' `
        --output json | ConvertFrom-Json

    Write-Host "`nDeployment Outputs:" -ForegroundColor Cyan
    foreach ($Output in $Outputs) {
        Write-Host "$($Output.OutputKey): $($Output.OutputValue)"
    }
} else {
    Write-Error "Stack deployment failed"
    exit 1
}

Write-Host "`n[OK] Deployment complete!" -ForegroundColor Green
