# Lantern OS v1.0.0 — Production Deployment Guide

## Permanent URL Options

### Option 1: fly.io (Recommended for Speed)
- **Setup time**: 15 minutes
- **Cost**: Free tier available, $5/month for production
- **Features**: Automatic scaling, built-in monitoring, global CDN
- **URL Format**: `https://lantern-os.fly.dev` (or custom domain)

### Option 2: AWS ECS (Full Control)
- **Setup time**: 1-2 hours
- **Cost**: $20-100/month for small deployment
- **Features**: Full AWS ecosystem, CloudFormation IaC, Fargate serverless
- **URL Format**: Custom domain or ALB DNS

---

## Deploy to fly.io (Fastest Path)

### Prerequisites
```bash
# Install fly CLI
# macOS
brew install flyctl

# Linux/Windows
# Download from https://fly.io/docs/hands-on/install/

# Authenticate
fly auth login
```

### 1. Create fly.toml
```toml
# fly.toml
app = "lantern-os"
primary_region = "iad"  # US East

[build]
  dockerfile = "Dockerfile.omni-unified"

[env]
  LANTERN_MODE = "production"
  FLASK_ENV = "production"

[http_service]
  internal_port = 5000
  force_https = true
  auto_start_machines = true
  auto_stop_machines = true
  min_machines_running = 1

[[services]]
  protocol = "tcp"
  internal_port = 5000
  ports = [{ port = 80, handlers = ["http"], force_https = true }]
  ports = [{ port = 443, handlers = ["tls", "http"], force_https = true }]

[[services]]
  protocol = "tcp"
  internal_port = 4177
  ports = [{ port = 8080 }]

[[services]]
  protocol = "tcp"
  internal_port = 8765
  ports = [{ port = 8081 }]

[[services]]
  protocol = "tcp"
  internal_port = 8000
  ports = [{ port = 8082 }]

[[services]]
  protocol = "tcp"
  internal_port = 8767
  ports = [{ port = 8083 }]

[deploy]
  strategy = "rolling"

[checks.http]
  grace_period = "60s"
  interval = "10s"
  method = "GET"
  path = "/health"
  protocol = "http"
  timeout = "5s"

[statics]
  guest_path = "/app/public"
  url_prefix = "/static"
```

### 2. Deploy to fly.io
```bash
# Create app
fly launch --name lantern-os --region iad --build-only

# Deploy
fly deploy

# Monitor
fly logs
fly status
```

### 3. Configure Custom Domain (Optional)
```bash
# Add custom domain
fly certs add lantern.your-domain.com

# Update DNS
# CNAME lantern.your-domain.com → lantern-os.fly.dev
```

### Result
```
✅ Production URL: https://lantern-os.fly.dev
✅ Dashboard: https://lantern-os.fly.dev:8080
✅ Browser STT: https://lantern-os.fly.dev:8081
✅ Orchestrator: https://lantern-os.fly.dev:8082
✅ RAG Server: https://lantern-os.fly.dev:8083
```

---

## Deploy to AWS ECS (Full Control)

### Prerequisites
```bash
# Install AWS CLI
aws --version

# Configure credentials
aws configure

# Install CDK
npm install -g aws-cdk
```

### 1. Create CDK Stack
```typescript
// infra/lib/lantern-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elasticloadbalancingv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as route53 from 'aws-cdk-lib/aws-route53';

export class LanternStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC
    const vpc = new ec2.Vpc(this, 'LanternVpc', {
      maxAzs: 2,
      cidrMask: 24,
    });

    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'LanternCluster', {
      vpc,
      clusterName: 'lantern-cluster',
    });

    // Task Definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'LanternTask', {
      memoryLimitMiB: 2048,
      cpu: 1024,
    });

    taskDefinition.addContainer('lantern', {
      image: ecs.ContainerImage.fromRegistry('ghcr.io/alex-place/lantern-os:v1.0.0'),
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'lantern',
      }),
      portMappings: [
        { containerPort: 5000 },
        { containerPort: 4177 },
        { containerPort: 8765 },
        { containerPort: 8000 },
        { containerPort: 8767 },
      ],
    });

    // Fargate Service
    const service = new ecs.FargateService(this, 'LanternService', {
      cluster,
      taskDefinition,
      serviceName: 'lantern-service',
      desiredCount: 1,
      assignPublicIp: false,
    });

    // Load Balancer
    const lb = new elasticloadbalancingv2.ApplicationLoadBalancer(this, 'LB', {
      vpc,
      internetFacing: true,
    });

    // Health Check Target Group
    const tg5000 = new elasticloadbalancingv2.ApplicationTargetGroup(this, 'TG5000', {
      vpc,
      targetType: elasticloadbalancingv2.TargetType.IP,
      port: 5000,
      healthCheck: {
        path: '/health',
        healthyHttpCodes: '200',
      },
    });

    service.attachToApplicationTargetGroup(tg5000);

    // Listener
    lb.addListener('ListenerHTTPS', {
      port: 443,
      protocol: elasticloadbalancingv2.ApplicationProtocol.HTTPS,
      certificates: [/* your ACM cert */],
      defaultTargetGroups: [tg5000],
    });

    // Output
    new cdk.CfnOutput(this, 'LoadBalancerDNS', {
      value: lb.loadBalancerDnsName,
    });
  }
}
```

### 2. Deploy Stack
```bash
# Synthesize
cdk synth

# Deploy
cdk deploy

# Monitor
aws logs tail /ecs/lantern --follow
```

### Result
```
✅ Production URL: https://lantern-alb-xxxxx.us-east-1.elb.amazonaws.com
✅ Custom Domain: lantern.your-domain.com (via Route53)
✅ Scaling: Auto-scales 1-5 instances
✅ Monitoring: CloudWatch integrated
```

---

## Permanent URL Setup

### After Deployment

1. **Update .env.production**
```bash
# For fly.io
LANTERN_API_URL=https://lantern-os.fly.dev
LANTERN_DASHBOARD_URL=https://lantern-os.fly.dev:8080
LANTERN_BROWSER_URL=https://lantern-os.fly.dev:8081

# For AWS
LANTERN_API_URL=https://lantern.your-domain.com
LANTERN_DASHBOARD_URL=https://lantern-dashboard.your-domain.com
LANTERN_BROWSER_URL=https://lantern-browser.your-domain.com
```

2. **Update Documentation**
```markdown
## Production URLs

| Service | URL |
|---------|-----|
| API | https://lantern-os.fly.dev |
| Dashboard | https://lantern-os.fly.dev:8080 |
| Browser | https://lantern-os.fly.dev:8081 |
| Orchestrator | https://lantern-os.fly.dev:8082 |
| RAG Server | https://lantern-os.fly.dev:8083 |
```

3. **Update Agent Slots**
- Set `LANTERN_PUBLIC_URL` in all 4 agent slot configs
- Update batch sync job to use production URLs
- Update documentation links

4. **DNS Configuration**
```bash
# If using custom domain
# Add A/CNAME record pointing to your hosting provider
lantern.your-domain.com → lantern-os.fly.dev (CNAME)
# or
lantern.your-domain.com → ALB IP (A record for AWS)
```

---

## Monitoring & Maintenance

### fly.io
```bash
# Check status
fly status

# View logs
fly logs -a lantern-os

# Scale up
fly scale count 3

# Update certificate
fly certs show
```

### AWS
```bash
# Check ECS service
aws ecs describe-services \
  --cluster lantern-cluster \
  --services lantern-service

# View logs
aws logs tail /ecs/lantern --follow

# Scale up
aws ecs update-service \
  --cluster lantern-cluster \
  --service lantern-service \
  --desired-count 3
```

---

## Post-Deployment Checklist

- [ ] Health checks passing on production
- [ ] All 5 services responding on permanent URLs
- [ ] SSL/TLS certificates valid
- [ ] Monitoring/logging configured
- [ ] Auto-scaling rules set
- [ ] Backup procedures in place
- [ ] DNS records updated (if custom domain)
- [ ] Agent slots configured with permanent URLs
- [ ] Documentation updated with production URLs
- [ ] Code freeze activated
- [ ] Incident response procedures documented

---

## Costs Comparison

| Provider | Setup | Monthly | Notes |
|----------|-------|---------|-------|
| fly.io | 5 min | $5 | Easiest, built-in scaling |
| AWS ECS | 1-2 hrs | $25-100 | More control, RDS + cache needed |
| AWS Free Tier | 1-2 hrs | $0 (1 yr) | Limited to 750 hrs/month ECS |

---

## Rollback Procedure

**fly.io:**
```bash
# Revert to previous release
fly releases
fly releases rollback
```

**AWS:**
```bash
# Rollback CloudFormation
aws cloudformation cancel-update-stack --stack-name lantern-os-stack
# or
aws cloudformation delete-stack --stack-name lantern-os-stack
cdk deploy # with previous version
```

---

**Next Steps:**
1. Choose deployment platform (fly.io recommended for speed)
2. Get permanent domain name
3. Execute deployment
4. Update all URLs in documentation
5. Activate code freeze with permanent URLs live

