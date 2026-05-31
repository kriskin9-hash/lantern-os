# AWS MCP Setup for Windsurf

Status: held - requires operator configuration

This guide adds AWS MCP (Model Context Protocol) servers to Windsurf for Lantern OS cloud operations.

## Simple Answer

AWS MCP allows Cascade AI to query AWS resources, read documentation, and manage infrastructure through natural language. This is configured in **held** state until you complete the safety checklist.

## Safety Checklist (Required)

- [ ] AWS credentials configured (IAM user, not root)
- [ ] Windsurf MCP canary test passed
- [ ] Local-only mode enabled initially
- [ ] `allowToolExecution: false` until validated
- [ ] Evidence receipt generated after first test

## Prerequisites

1. **AWS Account** with IAM user (not root)
2. **AWS CLI** installed locally
3. **Windsurf IDE** with MCP support
4. **Lantern OS safety hooks** active (see `.windsurf/hooks.json`)

## Step 1: Configure AWS Credentials

Create or edit your AWS credentials file:

```powershell
# Check if credentials exist
Get-Content ~/.aws/credentials

# Or set environment variables
$env:AWS_ACCESS_KEY_ID = "your-key-id"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

**Security boundary**: Never commit credentials to git. Use environment variables or AWS IAM Identity Center.

## Step 2: Install AWS MCP Server

Based on the web search results, you have two options:

### Option A: AWS Toolkit Extension (Recommended for Windsurf)

1. Open Windsurf
2. Go to Extensions panel
3. Search for "AWS Toolkit"
4. Install and sign in with AWS credentials

### Option B: AWS MCP Server (via npm/pip)

```bash
# AWS CLI MCP Server
npm install -g @aws/mcp-server

# Or Python version
pip install aws-mcp-server
```

## Step 3: Configure Windsurf MCP Config

Edit your Windsurf MCP configuration:

1. Open Windsurf Settings
2. Go to MCP Servers
3. Click "View raw config"
4. Add the AWS MCP server configuration:

```json
{
  "mcpServers": {
    "aws-cli": {
      "command": "npx",
      "args": ["-y", "@aws/mcp-server"],
      "env": {
        "AWS_ACCESS_KEY_ID": "${AWS_ACCESS_KEY_ID}",
        "AWS_SECRET_ACCESS_KEY": "${AWS_SECRET_ACCESS_KEY}",
        "AWS_DEFAULT_REGION": "${AWS_DEFAULT_REGION}"
      }
    }
  }
}
```

**Note**: Use environment variable references, not hardcoded values.

## Step 4: Update Lantern OS MCP Sources

After configuring Windsurf, update the Lantern OS MCP sources:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-LanternMcpConnector.ps1
```

This validates:
- AWS MCP server reachable
- Credentials authenticated
- Tool discovery successful
- Safety boundaries intact

## Step 5: Run Canary Test

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-McpCanaryTest.ps1 -Provider aws
```

Expected outputs:
- Connection status: **held** until validated
- Tool count: 0 until canary passes
- Validation receipt: generated in `manifests/validation/`

## Evidence / Source Discipline

**What this enables**:
- Query AWS resources (EC2, S3, Lambda status)
- Read AWS documentation inline
- Generate Terraform/CloudFormation templates
- Check service limits and costs

**What this does NOT enable** (until explicitly configured):
- Automatic resource creation
- Production deployments
- Cost-incurring operations
- Cross-account access

## Proven / Held / Local-Only

| State | Status | Reason |
|-------|--------|--------|
| AWS credentials | held | Requires operator to configure |
| MCP connection | held | Server not yet installed |
| Canary test | held | No evidence receipt yet |
| Tool execution | blocked | Safety gate requires manual enable |

## Next Safe Action

1. Verify AWS credentials are configured: `aws sts get-caller-identity`
2. Install AWS MCP server in Windsurf
3. Run canary test to generate evidence receipt
4. Update `manifests/lantern-mcp-sources.json` to set `enabled: true`

## Validation Path

After setup, evidence should appear in:
- `manifests/validation/MCP-CONNECTOR-LATEST.json`
- `manifests/evidence/aws-mcp-canary-*.md`
- Fleet health dashboard showing MCP status

## Rollback

If issues occur:
1. Set `enabled: false` in `lantern-mcp-sources.json`
2. Remove MCP server from Windsurf config
3. Revoke AWS credentials if compromised
4. Run convergence loop to validate state

---

**Related**: 
- `docs/MCP-CONNECTOR.md` - General MCP safety contract
- `manifests/lantern-mcp-sources.json` - Source definitions
- `scripts/Test-LanternMcpConnector.ps1` - Validation script
