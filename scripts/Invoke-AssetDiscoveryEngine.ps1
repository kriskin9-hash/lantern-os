param(
    [string]$ScanPath = "D:\tmp\lantern-os",
    [string]$OutputPath = "D:\tmp\lantern-os\data\automation\asset-discovery-results.json",
    [string[]]$AdditionalRepos = @(
        "C:\tmp\human-flourishing-frameworks-scan",
        "C:\Users\alexp\Documents\gm-agent-orchestrator"
    ),
    [switch]$RunOnce,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    
    $logPath = "D:\tmp\lantern-os\data\automation\asset-discovery.log"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logPath -Value $logMessage -ErrorAction SilentlyContinue
}

function Test-RepoPath {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        return $false
    }
    
    Push-Location $Path -ErrorAction SilentlyContinue
    try {
        git rev-parse --git-dir 2>$null | Out-Null
        $exitCode = $LASTEXITCODE
        return $exitCode -eq 0
    }
    catch {
        return $false
    }
    finally {
        Pop-Location -ErrorAction SilentlyContinue
    }
}

function Get-AssetInventory {
    param([string]$RepoPath, [string]$RepoName)
    
    Write-Log "Scanning $RepoName at $RepoPath"
    
    $assets = @{
        repoName = $RepoName
        repoPath = $RepoPath
        scannedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        categories = @{}
        totalFiles = 0
        commercialViabilityScore = 0
    }
    
    Push-Location $RepoPath
    try {
        # Count total files
        $assets.totalFiles = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue).Count
        
        # Scan for specific asset categories
        $categories = @{
            skills = @{
                path = "skills"
                pattern = "SKILL.md"
                found = @()
                viability = "high"
            }
            reports = @{
                path = "reports"
                pattern = "*.md"
                found = @()
                viability = "high"
            }
            offers = @{
                path = "offers"
                pattern = "*.md"
                found = @()
                viability = "high"
            }
            scripts = @{
                path = "scripts"
                pattern = "*.ps1"
                found = @()
                viability = "medium"
            }
            apps = @{
                path = "apps"
                pattern = "*"
                found = @()
                viability = "medium"
                excludePattern = "node_modules"
            }
            docs = @{
                path = "docs"
                pattern = "*.md"
                found = @()
                viability = "low"
            }
            surfaces = @{
                path = "surfaces"
                pattern = "*.html"
                found = @()
                viability = "medium"
            }
            data = @{
                path = "data"
                pattern = "*.json"
                found = @()
                viability = "low"
            }
        }
        
        foreach ($catKey in $categories.Keys) {
            $cat = $categories[$catKey]
            $searchPath = Join-Path $RepoPath $cat.path
            
            if (Test-Path $searchPath) {
                $files = Get-ChildItem -Path $searchPath -Filter $cat.pattern -Recurse -ErrorAction SilentlyContinue |
                    Where-Object { $_.FullName -notlike '*\node_modules\*' }
                $cat.found = $files | Select-Object -ExpandProperty FullName
                
                # Calculate category metrics
                $cat.count = $files.Count
                $cat.lastModified = if ($files) { ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime.ToString("yyyy-MM-dd") } else { $null }
            }
            else {
                $cat.count = 0
                $cat.found = @()
            }
            
            $assets.categories[$catKey] = $cat
        }
        
        # Calculate commercial viability score
        $score = 0
        $score += [int]($assets.categories['skills'].count) * 10
        $score += [int]($assets.categories['reports'].count) * 5
        $score += [int]($assets.categories['offers'].count) * 15
        $score += [int]($assets.categories['scripts'].count) * 3
        $score += [int]($assets.categories['surfaces'].count) * 5
        $score += [int]($assets.categories['apps'].count) * 8
        
        $assets.commercialViabilityScore = [Math]::Min($score, 100)
        
        # Identify top commercial assets
        $assets.topAssets = @()
        
        # Check for specific high-value indicators
        $highValueFiles = @(
            "FASTEST-PATHS-FIRST-200-DIGITAL-ASSETS",
            "COMET-LEAP",
            "CASH-SPRINT",
            "SKILL.md",
            "PERFECT-REPORT",
            "offer-sheet",
            "pilot"
        )
        
        foreach ($indicator in $highValueFiles) {
            $fileMatches = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | 
                Where-Object { $_.Name -like "*$indicator*" }
            
            foreach ($match in $fileMatches) {
                $assets.topAssets += @{
                    name = $match.Name
                    path = $match.FullName
                    type = "high-value-indicator"
                    indicator = $indicator
                }
            }
        }
        
        return $assets
    }
    finally {
        Pop-Location
    }
}

function Get-MarketContext {
    # Return cached market context (would integrate with external APIs in full implementation)
    return @{
        lastUpdated = Get-Date -Format "yyyy-MM-dd"
        sources = @(
            "Census BTOS - SMB AI adoption ~17-20%",
            "U.S. Chamber 2025 - 60% SMB using AI for operations",
            "Pew 2025 - 3.4% K-12 students homeschooled",
            "Johns Hopkins 2024-25 - Homeschooling grew 4.9%"
        )
        demandSignals = @(
            @{ category = 'AI setup/training'; demand = 'high'; priceRange = '$199-$499' },
            @{ category = 'repo/RAG cleanup'; demand = 'high'; priceRange = '$199-$299' },
            @{ category = 'founder reports'; demand = 'medium'; priceRange = '$149-$299' },
            @{ category = 'homeschool packets'; demand = 'medium'; priceRange = '$49-$149' }
        )
    }
}

function Get-MonetizationRecommendations {
    param([object]$Assets)
    
    $recommendations = @()
    
    # Skill-based offers
    if ($Assets.categories.skills.count -gt 0) {
        $recommendations += @{
            type = "skill-sprint"
            name = "Repo/RAG Cleanup Sprint"
            price = '$199-$299'
            timeToCash = "1-3 days"
            assetsRequired = $Assets.categories.skills.found | Select-Object -First 3
            confidence = "high"
        }
    }
    
    # Report-based offers
    if ($Assets.categories.reports.count -gt 0) {
        $recommendations += @{
            type = "report-pack"
            name = "Founder Report Pack"
            price = '$199-$299'
            timeToCash = "1-4 days"
            assetsRequired = $Assets.categories.reports.found | Select-Object -First 3
            confidence = "high"
        }
    }
    
    # Script-based offers
    if ($Assets.categories.scripts.count -gt 0) {
        $recommendations += @{
            type = "setup-session"
            name = "Local-first AI / MCP Audit & Setup"
            price = '$199-$499'
            timeToCash = "Same day-3 days"
            assetsRequired = $Assets.categories.scripts.found | Select-Object -First 3
            confidence = "medium"
        }
    }
    
    return $recommendations
}

function Invoke-AssetDiscoveryEngine {
    Write-Log "=== Asset Discovery Engine Started ==="
    
    if ($DryRun) {
        Write-Log "DRY RUN MODE - No files will be written"
    }
    
    # Collect all repos to scan
    $reposToScan = @(@{ path = $ScanPath; name = "lantern-os" })
    
    foreach ($repo in $AdditionalRepos) {
        $repoName = Split-Path $repo -Leaf
        $reposToScan += @{ path = $repo; name = $repoName }
    }
    
    # Scan each repo
    $allAssets = @()
    foreach ($repo in $reposToScan) {
        if (Test-RepoPath -Path $repo.path) {
            $assets = Get-AssetInventory -RepoPath $repo.path -RepoName $repo.name
            $allAssets += $assets
        }
        else {
            Write-Log "Repository not found or not a git repo: $($repo.path)" "WARN"
        }
    }
    
    # Get market context
    $marketContext = Get-MarketContext
    
    # Generate recommendations for each repo
    $allRecommendations = @()
    foreach ($asset in $allAssets) {
        $recs = Get-MonetizationRecommendations -Assets $asset
        $allRecommendations += @{
            repo = $asset.repoName
            viabilityScore = $asset.commercialViabilityScore
            recommendations = $recs
        }
    }
    
    # Compile results
    $totalFileCount = 0
    foreach ($assetItem in $allAssets) {
        if ($assetItem -and ($assetItem -is [hashtable]) -and $assetItem.ContainsKey('totalFiles')) {
            $totalFileCount += $assetItem.totalFiles
        } elseif ($assetItem -and ($assetItem.PSObject.Properties['totalFiles'])) {
            $totalFileCount += $assetItem.totalFiles
        }
    }
    
    $results = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Asset Discovery Engine v1.0"
        mode = if ($DryRun) { "dry-run" } else { "live" }
        reposScanned = $allAssets.Count
        totalAssets = $totalFileCount
        marketContext = $marketContext
        assets = $allAssets
        monetizationRecommendations = $allRecommendations
        topOpportunities = $allRecommendations | 
            ForEach-Object { $_.recommendations } | 
            Where-Object { $_ -ne $null } |
            Sort-Object -Property @{Expression={
                switch ($_.confidence) {
                    "high" { 3 }
                    "medium" { 2 }
                    "low" { 1 }
                    default { 0 }
                }
            }} -Descending |
            Group-Object -Property name | ForEach-Object { $_.Group | Select-Object -First 1 } |
            Select-Object -First 5
        nextAction = "Review top opportunities and select one to package for outreach"
    }
    
    # Write results
    if (-not $DryRun) {
        $outputDir = Split-Path $OutputPath -Parent
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
        
        $results | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
        Write-Log "Results written to $OutputPath"
    }
    else {
        Write-Log "DRY RUN: Would write results to $OutputPath"
        $results | ConvertTo-Json -Depth 10 | Write-Host
    }
    
    # Summary output
    Write-Log "=== Discovery Summary ==="
    Write-Log "Repos scanned: $($results.reposScanned)"
    Write-Log "Total files: $($results.totalAssets)"
    Write-Log "Top opportunities:"
    foreach ($opp in $results.topOpportunities) {
        Write-Log "  - $($opp.name) [$($opp.confidence)] - $($opp.price)"
    }
    Write-Log "Next action: $($results.nextAction)"
    
    return $results
}

# Main execution
if ($RunOnce) {
    Invoke-AssetDiscoveryEngine
}
else {
    Write-Log "RunOnce not specified. Use -RunOnce for single execution."
}
