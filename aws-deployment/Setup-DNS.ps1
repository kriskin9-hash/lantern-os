# Setup-DNS.ps1
# Configures Route53 DNS for Lantern OS domain

param(
    [string]$DomainName = "lantern-os.app",
    [string]$ALBDNSName = "",
    [string]$Region = "us-east-1",
    [switch]$DryRun
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

function Get-ALBDNSName {
    if ($ALBDNSName) {
        return $ALBDNSName
    }

    Write-Step "Retrieving ALB DNS name from CloudFormation..."

    try {
        $stack = aws cloudformation describe-stacks `
            --stack-name "lantern-os-stack" `
            --region $Region 2>&1 | ConvertFrom-Json

        $outputs = @{}
        $stack.Stacks[0].Outputs | ForEach-Object {
            $outputs[$_.OutputKey] = $_.OutputValue
        }

        if ($outputs.ContainsKey("LoadBalancerDNS")) {
            Write-Success "Found ALB: $($outputs.LoadBalancerDNS)"
            return $outputs.LoadBalancerDNS
        } else {
            Write-Error "Could not find LoadBalancerDNS in stack outputs"
            exit 1
        }
    } catch {
        Write-Error "Failed to retrieve stack: $_"
        exit 1
    }
}

function Create-HostedZone {
    param([string]$Domain)

    Write-Step "Checking if hosted zone exists for $Domain..."

    try {
        $zones = aws route53 list-hosted-zones-by-name `
            --dns-name $Domain `
            --region $Region 2>&1 | ConvertFrom-Json

        if ($zones.HostedZones.Count -gt 0) {
            $zoneId = $zones.HostedZones[0].Id -replace "/hostedzone/", ""
            Write-Success "Hosted zone already exists: $zoneId"
            return $zoneId
        }
    } catch {
        # Zone doesn't exist, proceed to create
    }

    Write-Step "Creating hosted zone for $Domain..."

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create hosted zone"
        return "z-dummy-zone-id"
    }

    try {
        $zoneOutput = aws route53 create-hosted-zone `
            --name $Domain `
            --caller-reference "lantern-$(Get-Date -Format 'yyyyMMddHHmmss')" `
            --region $Region 2>&1 | ConvertFrom-Json

        $zoneId = $zoneOutput.HostedZone.Id -replace "/hostedzone/", ""
        Write-Success "Hosted zone created: $zoneId"

        Write-Step "Nameservers for your domain registrar:"
        $zoneOutput.DelegationSet.NameServers | ForEach-Object {
            Write-Host "  - $_"
        }

        return $zoneId
    } catch {
        Write-Error "Failed to create hosted zone: $_"
        exit 1
    }
}

function Create-CNAMERecord {
    param(
        [string]$ZoneId,
        [string]$DomainName,
        [string]$ALBDNSName
    )

    Write-Step "Creating CNAME record: $DomainName → $ALBDNSName"

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create CNAME record"
        return
    }

    $recordSet = @{
        Action = "CREATE"
        ResourceRecordSet = @{
            Name = $DomainName
            Type = "CNAME"
            TTL = 300
            ResourceRecords = @(
                @{ Value = $ALBDNSName }
            )
        }
    } | ConvertTo-Json -Depth 5

    Write-Host "  Record configuration:"
    $recordSet | ConvertFrom-Json | ForEach-Object {
        Write-Host "    Name: $($_.ResourceRecordSet.Name)"
        Write-Host "    Type: $($_.ResourceRecordSet.Type)"
        Write-Host "    Target: $($_.ResourceRecordSet.ResourceRecords[0].Value)"
    }

    try {
        $tempFile = New-TemporaryFile
        $recordSet | Set-Content -Path $tempFile.FullName -Force

        aws route53 change-resource-record-sets `
            --hosted-zone-id $ZoneId `
            --change-batch "file://$($tempFile.FullName)" `
            --region $Region | Out-Null

        Remove-Item $tempFile.FullName -Force

        Write-Success "CNAME record created"
        Write-Host "  Status: PENDING (may take 1-5 minutes to propagate)"
    } catch {
        Write-Error "Failed to create CNAME record: $_"
        exit 1
    }
}

function Verify-DNS {
    param([string]$DomainName)

    Write-Step "Verifying DNS resolution (this may take a moment)..."

    $maxAttempts = 12  # 60 seconds total (5 second intervals)
    $attempt = 0

    while ($attempt -lt $maxAttempts) {
        try {
            $result = Resolve-DnsName -Name $DomainName -ErrorAction SilentlyContinue
            if ($result) {
                Write-Success "DNS resolved: $($result.IP4Address)"
                return $true
            }
        } catch {
            # DNS not yet resolved
        }

        $attempt++
        if ($attempt -lt $maxAttempts) {
            Write-Host "  Attempt $attempt/$maxAttempts - DNS not yet propagated, retrying..."
            Start-Sleep -Seconds 5
        }
    }

    Write-Host "  ⚠ DNS resolution pending (usually takes 5-10 minutes)"
    Write-Host "  Verify with: nslookup $DomainName"
    return $false
}

function Test-HTTPAccess {
    param([string]$Url)

    Write-Step "Testing HTTP access to $Url"

    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -ErrorAction SilentlyContinue
        Write-Success "HTTP access successful (Status: $($response.StatusCode))"
        return $true
    } catch {
        Write-Host "  ⚠ HTTP access not yet available"
        Write-Host "  Reason: $($_.Exception.Message)"
        return $false
    }
}

# Main execution
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  LANTERN OS — Route53 DNS Setup                              ║" -ForegroundColor Magenta
Write-Host "║  Domain: $DomainName" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

$albDNS = Get-ALBDNSName
$zoneId = Create-HostedZone -Domain $DomainName
Create-CNAMERecord -ZoneId $zoneId -DomainName $DomainName -ALBDNSName $albDNS

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "📋 DNS Setup Summary" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "✅ Hosted Zone ID: $zoneId"
Write-Host "✅ CNAME Record: $DomainName → $albDNS"
Write-Host ""
Write-Host "📌 Important:"
Write-Host "  1. Update your domain registrar nameservers (if new zone)"
Write-Host "  2. DNS propagation takes 5-10 minutes"
Write-Host "  3. Test with: nslookup $DomainName"
Write-Host "  4. Access your app at: https://$DomainName"
Write-Host ""

if (-not $DryRun) {
    Write-Host "🔄 Verifying DNS..." -ForegroundColor Cyan
    Verify-DNS -DomainName $DomainName

    Write-Host ""
    Write-Host "🌐 Next: Enable HTTPS" -ForegroundColor Cyan
    Write-Host "  1. Create ACM certificate for $DomainName"
    Write-Host "  2. Update ALB listener to use HTTPS"
    Write-Host "  3. Update .env.production to use https://"
}

Write-Host ""
Write-Host "✅ DNS setup complete!" -ForegroundColor Green
Write-Host ""
