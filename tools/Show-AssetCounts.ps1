$r = Get-Content 'D:\tmp\lantern-os\data\automation\asset-discovery-results.json' -Raw | ConvertFrom-Json
foreach ($a in $r.assets) {
    Write-Host ("=== " + $a.repoName + "  score=" + $a.commercialViabilityScore + "  totalFiles=" + $a.totalFiles + " ===")
    foreach ($k in @('skills','reports','offers','scripts','apps','surfaces','docs','data')) {
        $c = $a.categories.$k
        if ($c) { Write-Host ("  " + $k + ": " + $c.count) }
    }
    Write-Host ("  top assets: " + $a.topAssets.Count)
}
Write-Host ""
Write-Host "=== Top 5 Opportunities ==="
foreach ($o in $r.topOpportunities) {
    Write-Host ("  [" + $o.confidence + "] " + $o.name + " / " + $o.price + " / " + $o.timeToCash)
}
