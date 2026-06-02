# Lantern OS v1.0.0 — AWS ECS Deployment Guide

## Overview

This guide walks you through deploying Lantern OS to AWS ECS (Elastic Container Service) with a permanent domain name, auto-scaling, monitoring, and production-grade infrastructure.

**Deployment Time**: ~20 minutes (setup) + 15 minutes (stack creation) = ~35 minutes total  
**Cost**: ~$25–50/month for the production setup  
**Domain**: `lantern-os.app` (changeable)

---

## Prerequisites

### Required
1. **AWS Account** — with permissions to create:
   - VPC, subnets, security groups
   - EC2, ECS, ALB
   - CloudFormation stacks
   - Route53 hosted zones
   - CloudWatch logs and alarms

2. **AWS CLI v2** — [Install](https://aws.amazon.com/cli/)
   ```bash
   aws --version
   aws configure  # Set your access key, secret, and default region
   ```

3. **Docker Image Published** — `ghcr.io/alex-place/lantern-os:v1.0.0`
   - Already built during v1.0.0 release
   - Verify with: `docker pull ghcr.io/alex-place/lantern-os:v1.0.0`

4. **Domain (optional)**
   - Already set to `lantern-os.app` in the CloudFormation template
   - Can be changed to any domain you own

---

## Step 1: Validate AWS Setup

```bash
# Verify AWS CLI is installed
aws --version

# Verify credentials are configured
aws sts get-caller-identity
# Should output your AWS Account ID and ARN

# Verify you're in the correct region
aws configure get region
# Should show: us-east-1 (or your preferred region)
```

---

## Step 2: Prepare the Deployment

```bash
# Navigate to the deployment directory
cd /d/tmp/lantern-os/aws-deployment

# List deployment files
ls -la
# cloudformation-template.yaml    - Main infrastructure
# Deploy-ToAWS.ps1               - Deployment script
# Setup-DNS.ps1                  - DNS configuration
# AWS-DEPLOYMENT-GUIDE.md        - This file
```

---

## Step 3: Validate the CloudFormation Template

```powershell
# Validate the template (no changes made)
./Deploy-ToAWS.ps1 -ValidateOnly

# Should output:
# ✅ CloudFormation template found
# ✅ Template validation passed
```

---

## Step 4: Deploy to AWS (Dry Run)

```powershell
# Preview what will be created without making changes
./Deploy-ToAWS.ps1 -DryRun

# Expected output shows all resources that will be created
```

---

## Step 5: Deploy to Production

```powershell
# Execute the actual deployment
./Deploy-ToAWS.ps1 -StackName "lantern-os-stack" `
                  -Region "us-east-1" `
                  -AppName "lantern-os" `
                  -Environment "production" `
                  -DomainName "lantern-os.app"

# You'll be prompted: "Proceed with stack creation? (yes/no)"
# Type: yes

# Wait for stack creation to complete (~15 minutes)
# The script will poll CloudFormation every 30 seconds and show progress
```

### What Gets Created

| Resource | Type | Quantity |
|----------|------|----------|
| VPC | Network | 1 |
| Subnets | Network | 4 (2 public, 2 private) |
| Security Groups | Network | 2 |
| Load Balancer (ALB) | Networking | 1 |
| Target Groups | Load Balancing | 5 (ports 5000, 4177, 8765, 8000, 8767) |
| ECS Cluster | Container Orchestration | 1 |
| ECS Task Definition | Container | 1 |
| ECS Service | Container Runtime | 1 |
| CloudWatch Log Group | Monitoring | 1 |
| Auto Scaling Group | Scaling | 1 |
| CloudWatch Alarms | Monitoring | 2 |
| IAM Roles | Access Control | 2 |

---

## Step 6: Retrieve Stack Outputs

Once the stack is created, the script automatically shows you:

```
📋 Stack Outputs:
  LoadBalancerDNS: lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com
  ClusterName: lantern-os-cluster
  ServiceName: lantern-os-service
  LogGroupName: /ecs/lantern-os
  APIEndpoint: http://lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com:5000
  DashboardEndpoint: http://lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com:4177
  BrowserSTTEndpoint: http://lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com:8765
  OrchestratorEndpoint: http://lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com:8000
  RAGEndpoint: http://lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com:8767
```

---

## Step 7: Configure DNS (Route53)

```powershell
# Set up Route53 hosted zone and CNAME records
./Setup-DNS.ps1 -DomainName "lantern-os.app"

# The script will:
# 1. Retrieve the ALB DNS name from CloudFormation
# 2. Create a Route53 hosted zone (if needed)
# 3. Create CNAME record: lantern-os.app → ALB DNS
# 4. Verify DNS propagation (takes 5-10 minutes)
```

### Manual DNS Setup (if Route53 script doesn't work)

**Option A: Using Route53 (Recommended)**
1. Go to AWS Console → Route53 → Hosted Zones
2. Create a hosted zone for `lantern-os.app`
3. Note the 4 nameservers provided
4. Update your domain registrar to use these nameservers
5. Create a CNAME record:
   - Name: `lantern-os.app`
   - Type: CNAME
   - Value: `lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com`
   - TTL: 300

**Option B: Using Your Registrar (GoDaddy, Namecheap, etc.)**
1. Log in to your domain registrar
2. Create a CNAME record:
   - Name: `lantern-os` (or `@` for root)
   - Type: CNAME
   - Target: `lantern-os-alb-xxxxx.us-east-1.elb.amazonaws.com`
3. Wait 5-10 minutes for DNS propagation

### Verify DNS Resolution

```bash
# Check if DNS is propagated
nslookup lantern-os.app

# Should return the ALB IP address
# Server: 8.8.8.8
# Address: X.X.X.X
```

---

## Step 8: Enable HTTPS (SSL/TLS)

**Option A: Using AWS Certificate Manager (Recommended)**

```bash
# Request a public certificate
aws acm request-certificate \
    --domain-name lantern-os.app \
    --validation-method DNS \
    --region us-east-1

# The certificate will be in PENDING_VALIDATION state
# You'll need to add a DNS validation record (AWS shows you what to add)
# This takes a few minutes
```

Then update the CloudFormation template to use the certificate:
```yaml
ALBListener:
  Type: AWS::ElasticLoadBalancingV2::Listener
  Properties:
    Protocol: HTTPS
    Port: 443
    Certificates:
      - CertificateArn: arn:aws:acm:region:account:certificate/xxxxx
    DefaultActions:
      - Type: forward
        TargetGroupArn: !Ref TargetGroupPort5000
```

**Option B: Using Let's Encrypt (via Certbot)**

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot

# Request certificate
sudo certbot certonly --dns-route53 \
    -d lantern-os.app \
    --agree-tos \
    --email your@email.com

# Upload to AWS Certificate Manager
aws acm import-certificate \
    --certificate fileb://cert.pem \
    --certificate-chain fileb://chain.pem \
    --private-key fileb://privkey.pem
```

---

## Step 9: Update Application Configuration

Create `.env.production` in the Lantern OS root:

```bash
# Production environment variables
LANTERN_MODE=production
FLASK_ENV=production
AWS_REGION=us-east-1

# Permanent URLs
LANTERN_API_URL=https://lantern-os.app
LANTERN_DASHBOARD_URL=https://lantern-os.app:4177
LANTERN_BROWSER_URL=https://lantern-os.app:8765
LANTERN_ORCHESTRATOR_URL=https://lantern-os.app:8000
LANTERN_RAG_URL=https://lantern-os.app:8767

# AWS Services
AWS_ECS_CLUSTER=lantern-os-cluster
AWS_ECS_SERVICE=lantern-os-service

# Monitoring
CLOUDWATCH_LOG_GROUP=/ecs/lantern-os
CLOUDWATCH_REGION=us-east-1
```

Then rebuild and push the Docker image:

```bash
docker build -f Dockerfile.omni-unified -t ghcr.io/alex-place/lantern-os:v1.0.0-prod .
docker push ghcr.io/alex-place/lantern-os:v1.0.0-prod
```

---

## Step 10: Monitor and Test

### View Logs

```bash
# Stream logs in real-time
aws logs tail /ecs/lantern-os --follow

# Filter logs
aws logs tail /ecs/lantern-os --filter-pattern "ERROR"

# View last 100 lines
aws logs tail /ecs/lantern-os --max-items 100
```

### Check ECS Service Health

```bash
# View service status
aws ecs describe-services \
    --cluster lantern-os-cluster \
    --services lantern-os-service \
    --region us-east-1

# View running tasks
aws ecs list-tasks \
    --cluster lantern-os-cluster \
    --region us-east-1

# View task details
aws ecs describe-tasks \
    --cluster lantern-os-cluster \
    --tasks <task-arn> \
    --region us-east-1
```

### Test HTTP Endpoints

```bash
# Test API health
curl https://lantern-os.app/health

# Test each service
curl https://lantern-os.app:5000/health    # API
curl https://lantern-os.app:4177/          # Dashboard
curl https://lantern-os.app:8765/          # Browser STT
curl https://lantern-os.app:8000/health    # Orchestrator
curl https://lantern-os.app:8767/health    # RAG
```

### CloudWatch Alarms

Alarms are automatically created and will notify you if:
- Healthy host count drops below 1
- CPU utilization exceeds 80%

View in AWS Console:
```
CloudWatch → Alarms → lantern-os-health-alarm, lantern-os-high-cpu-alarm
```

---

## Step 11: Configure Auto-Scaling

The stack includes auto-scaling targets:
- **Min**: 2 tasks
- **Max**: 5 tasks
- **Target CPU**: 70%

Adjust in AWS Console:
```
ECS → Clusters → lantern-os-cluster → Services → lantern-os-service
  → Auto Scaling → Edit
```

---

## Maintenance and Operations

### Update the Application

```bash
# 1. Update code in /d/tmp/lantern-os
# 2. Rebuild and push Docker image
docker build -f Dockerfile.omni-unified -t ghcr.io/alex-place/lantern-os:v1.0.1 .
docker push ghcr.io/alex-place/lantern-os:v1.0.1

# 3. Update CloudFormation stack
aws cloudformation update-stack \
    --stack-name lantern-os-stack \
    --template-body file://cloudformation-template.yaml \
    --parameters ParameterKey=ContainerImage,ParameterValue=ghcr.io/alex-place/lantern-os:v1.0.1 \
    --region us-east-1

# 4. Monitor the update
aws cloudformation wait stack-update-complete --stack-name lantern-os-stack
```

### Scale Up/Down

```bash
# Manually scale the service
aws ecs update-service \
    --cluster lantern-os-cluster \
    --service lantern-os-service \
    --desired-count 5 \
    --region us-east-1
```

### View Stack Events

```bash
# See what's happening with your stack
aws cloudformation describe-stack-events \
    --stack-name lantern-os-stack \
    --region us-east-1
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check task logs
aws logs tail /ecs/lantern-os --follow

# Check task status
aws ecs list-tasks --cluster lantern-os-cluster
aws ecs describe-tasks --cluster lantern-os-cluster --tasks <task-arn>

# Common issues:
# 1. Image not found — verify ECR image is published
# 2. Port binding error — check security groups
# 3. Health check failing — check /health endpoint
```

### High CPU Usage

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ClusterName,Value=lantern-os-cluster \
    --start-time 2026-06-01T00:00:00Z \
    --end-time 2026-06-01T23:59:59Z \
    --period 300 \
    --statistics Average
```

### DNS Not Resolving

```bash
# Check Route53 records
aws route53 list-resource-record-sets --hosted-zone-id <zone-id>

# Verify CNAME is pointing to ALB
nslookup lantern-os.app

# If not resolved:
# 1. Verify domain registrar nameservers are updated
# 2. Wait 5-10 minutes for propagation
# 3. Try: aws route53 test-dns-answer --hosted-zone-id <zone-id> --record-name lantern-os.app --record-type CNAME
```

### SSL Certificate Issues

```bash
# Check certificate status
aws acm describe-certificate --certificate-arn <arn> --region us-east-1

# If PENDING_VALIDATION:
# 1. Add the DNS validation record to Route53
# 2. Wait a few minutes for validation
```

---

## Costs

### Estimated Monthly Costs

| Service | Quantity | Unit Cost | Total |
|---------|----------|-----------|-------|
| ECS (Fargate) | 2 tasks × 1024 CPU, 2048 MB | ~$0.04663/hr | $67.93 |
| ALB | 1 | ~$16.20 | $16.20 |
| Data Transfer | 100 GB out | $0.12/GB | $12.00 |
| CloudWatch Logs | 10 GB ingested | $0.50/GB | $5.00 |
| Route53 Hosted Zone | 1 | $0.50 | $0.50 |
| **Total** | | | **~$102/month** |

**Cost Optimization:**
- Use 1 task instead of 2 (saves ~$34/month)
- Use smaller task size (512 CPU, 1024 MB) for dev (saves ~$30/month)
- Use AWS Graviton2 instances (saves ~20%)

---

## Rollback Procedure

### Delete the Stack (Everything)

```bash
aws cloudformation delete-stack --stack-name lantern-os-stack --region us-east-1

# Monitor deletion
aws cloudformation wait stack-delete-complete --stack-name lantern-os-stack
```

### Revert to Previous Version

```bash
# Keep the stack, just update the image
aws cloudformation update-stack \
    --stack-name lantern-os-stack \
    --template-body file://cloudformation-template.yaml \
    --parameters ParameterKey=ContainerImage,ParameterValue=ghcr.io/alex-place/lantern-os:v1.0.0 \
    --region us-east-1
```

---

## Next Steps

1. ✅ Deploy infrastructure (CloudFormation)
2. ✅ Configure DNS (Route53)
3. ✅ Enable HTTPS (ACM)
4. ✅ Test endpoints
5. ✅ Set up monitoring (CloudWatch)
6. ✅ Configure alerts
7. Activate code freeze in Git
8. Announce production launch

---

## Support and Escalation

| Issue | Command | Doc |
|-------|---------|-----|
| Service logs | `aws logs tail /ecs/lantern-os --follow` | [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/) |
| Service status | `aws ecs describe-services --cluster lantern-os-cluster --services lantern-os-service` | [ECS](https://docs.aws.amazon.com/AmazonECS/) |
| Stack events | `aws cloudformation describe-stack-events --stack-name lantern-os-stack` | [CloudFormation](https://docs.aws.amazon.com/cloudformation/) |
| Alarms | AWS Console → CloudWatch → Alarms | [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/) |

---

**Status: Ready for Deployment**  
**Last Updated: 2026-06-01**  
**v1.0.0 Production Ready**
