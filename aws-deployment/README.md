# AWS Deployment — Lantern OS

Complete CloudFormation + ECS deployment for Lantern OS + HFF + Suzie Orchestrator.

## Prerequisites

- AWS account with verified credentials
- AWS CLI v2 installed and configured
- Docker installed
- PowerShell 7+ (or compatible shell)

## Quick Start

### 1. Set AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, region (us-east-1), output format (json)
```

### 2. Create RDS Password in Secrets Manager

```bash
aws secretsmanager create-secret \
    --name lantern-db-password \
    --secret-string '{"password":"YourSecurePassword123!"}' \
    --region us-east-1
```

### 3. Deploy to AWS

From the lantern-os root directory:

```powershell
.\scripts\Deploy-AWS-ECS.ps1 -Environment production -ImageTag v0.2-unified
```

The script will:
- Build the Docker image locally
- Push it to Amazon ECR
- Deploy the CloudFormation stack
- Create ECS cluster, RDS, Redis, ALB, and services
- Display the final URLs

### 4. Access Your Deployment

After deployment succeeds, you'll get URLs like:

- **API**: `http://lantern-alb-123456789.us-east-1.elb.amazonaws.com:5000`
- **Dashboard**: `http://lantern-alb-123456789.us-east-1.elb.amazonaws.com:4177`
- **Health**: `http://lantern-alb-123456789.us-east-1.elb.amazonaws.com:9000/health`

## CloudFormation Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| lantern-cluster | ECS Cluster | Container orchestration |
| lantern-service | ECS Service | Manages running tasks |
| lantern-db | RDS PostgreSQL | Persistent data |
| lantern-cache | ElastiCache Redis | Caching layer |
| lantern-alb | Application Load Balancer | Traffic routing |
| VPC, Subnets, Security Groups | Network Infrastructure | Networking |

## Environment Variables

The CloudFormation template sets:

- `FLASK_ENV`: production
- `DATABASE_URL`: Automatically configured
- `REDIS_URL`: Automatically configured
- `LANTERN_MODE`: convergence-unified

## Scaling

To scale the number of ECS tasks:

```powershell
.\scripts\Deploy-AWS-ECS.ps1 -Environment production -ImageTag v0.2-unified
# Modify DesiredCount in the script or use AWS Console
```

Or via AWS CLI:

```bash
aws ecs update-service \
    --cluster lantern-cluster \
    --service lantern-service \
    --desired-count 5 \
    --region us-east-1
```

## Monitoring

### CloudWatch Logs

```bash
aws logs tail /ecs/lantern-os --follow
```

### ECS Service Status

```bash
aws ecs describe-services \
    --cluster lantern-cluster \
    --services lantern-service \
    --region us-east-1
```

### ALB Health Check

```bash
curl http://lantern-alb-xxx.us-east-1.elb.amazonaws.com:9000/health
```

## Cleanup

To delete all resources and stop incurring charges:

```bash
aws cloudformation delete-stack \
    --stack-name lantern-os-stack \
    --region us-east-1
```

Wait for stack deletion to complete:

```bash
aws cloudformation wait stack-delete-complete \
    --stack-name lantern-os-stack \
    --region us-east-1
```

## Cost Estimation

Rough monthly costs (us-east-1):

| Resource | Type | Monthly Cost |
|----------|------|--------------|
| ECS Fargate (2x t3.medium) | Compute | ~$45 |
| RDS (t3.micro) | Database | ~$15 |
| ElastiCache (cache.t3.micro) | Cache | ~$20 |
| ALB | Load Balancer | ~$16 |
| Data Transfer | Egress | ~$10+ |
| **Total** | | **~$100-150/month** |

(Actual costs vary; use AWS Pricing Calculator for estimates)

## Troubleshooting

### Docker Build Fails

Check Dockerfile.unified syntax:
```bash
docker build -f Dockerfile.unified --dry-run .
```

### ECR Login Fails

Ensure credentials are valid:
```bash
aws sts get-caller-identity
```

### CloudFormation Deployment Fails

Check stack events:
```bash
aws cloudformation describe-stack-events \
    --stack-name lantern-os-stack \
    --region us-east-1
```

### ECS Tasks Won't Start

Check task logs:
```bash
aws logs get-log-events \
    --log-group-name /ecs/lantern-os \
    --log-stream-name <stream-name> \
    --region us-east-1
```

## CI/CD Integration

The `.github/workflows/deploy-aws.yml` workflow automatically deploys on push to master/main.

Add to GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Support

For issues, check AWS CloudFormation events or contact AWS Support.
