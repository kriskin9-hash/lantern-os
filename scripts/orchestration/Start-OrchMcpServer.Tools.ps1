function Get-OrchStatus {
    return Invoke-JsonScript -ScriptPath $StatusScript -Arguments @("-Root", $Root)
}

function ConvertTo-AgentAvailability {
    param([object]$Slot)
    $hasTask = $null -ne $Slot.currentTask
    $hasLimit = $null -ne $Slot.limit
    $hasLock = $null -ne $Slot.manualLock
    $state = [string]$Slot.state
    $available = ($state -in @("idle", "recent")) -and !$hasTask -and !$hasLimit -and !$hasLock
    $reason = "ready"
    if ($hasTask) { $reason = "has_active_task" }
    elseif ($hasLimit) { $reason = "usage_limited" }
    elseif ($hasLock) { $reason = "manual_lock" }
    elseif ($state -in @("sleeping", "blocked", "locked", "stale", "active", "disabled")) { $reason = $state }
    return [pscustomobject]@{
        slot = [string]$Slot.name
        state = $state
        available = [bool]$available
        reason = $reason
        statusText = [string]$Slot.statusText
        currentTask = $Slot.currentTask
        blocker = $Slot.blocker
        limit = $Slot.limit
        manualLock = $Slot.manualLock
        latestLog = $(if ($Slot.latestLog) { [pscustomobject]@{ name = $Slot.latestLog.name; lastWriteTime = $Slot.latestLog.lastWriteTime; ageMinutes = $Slot.latestLog.ageMinutes; importantLine = $Slot.latestLog.importantLine } } else { $null })
        nextAction = $(if ($Slot.nextAction) { $Slot.nextAction.action } else { "" })
    }
}

function Get-AgentStatusTool {
    $status = Get-OrchStatus
    $agents = @($status.slots | ForEach-Object { ConvertTo-AgentAvailability -Slot $_ })
    return [pscustomobject]@{
        generatedAt = $status.generatedAt
        state = $status.state
        headline = $status.headline
        counts = $status.counts
        availability = $status.availability
        agents = $agents
        availableAgents = @($agents | Where-Object { $_.available })
        unavailableAgents = @($agents | Where-Object { !$_.available })
        nextAction = $status.nextAction
    }
}

function Get-QueueSummaryTool {
    $status = Get-OrchStatus
    return [pscustomobject]@{
        generatedAt = $status.generatedAt
        counts = $status.counts
        nextAction = $status.nextAction
        availability = $status.availability
        queue = $status.tasks.queue
        active = $status.tasks.active
        failed = $status.tasks.failed
        done = @($status.tasks.done | Select-Object -First 20)
    }
}

function Get-RecentFailuresTool {
    param([int]$Limit = 10)
    $status = Get-OrchStatus
    return [pscustomobject]@{ generatedAt = $status.generatedAt; failed = @($status.tasks.failed | Select-Object -First $Limit); blockedSlots = @($status.slots | Where-Object { $_.state -in @("blocked", "sleeping", "locked", "stale") } | Select-Object -First $Limit); priorityWarnings = $status.priorityWarnings }
}

function Get-LatestAgentLogsTool {
    $status = Get-OrchStatus
    return [pscustomobject]@{
        generatedAt = $status.generatedAt
        logs = @($status.slots | ForEach-Object { [pscustomobject]@{ slot = $_.name; state = $_.state; latestLog = $(if ($_.latestLog) { [pscustomobject]@{ name = $_.latestLog.name; path = $_.latestLog.path; lastWriteTime = $_.latestLog.lastWriteTime; ageMinutes = $_.latestLog.ageMinutes; importantLine = $_.latestLog.importantLine; tail = $_.latestLog.tail } } else { $null }) } })
    }
}

function Get-McpCapabilityStatusTool {
    return Invoke-JsonScript -ScriptPath $CapabilityStatusScript -Arguments @("-Root", $Root, "-Port", [string]$Port)
}

function Get-TunnelCanaryStatusTool {
    return [pscustomobject]@{
        ok = $false
        action = "orch_tunnel_canary"
        generatedAt = (Get-Date).ToString("o")
        root = $Root
        allowRemote = $true
        local = [pscustomobject]@{
            lane = "local"
            url = "http://127.0.0.1:$Port/mcp"
            ok = $false
            statusCode = $null
            toolCount = 0
            requiredToolsVisible = $false
            tools = @()
            error = "in_band_mcp_self_probe_deadlock_risk"
        }
        tunnel = [pscustomobject]@{
            lane = "tunnel"
            url = ""
            ok = $false
            statusCode = $null
            toolCount = 0
            requiredToolsVisible = $false
            tools = @()
            error = "out_of_band_probe_required"
        }
        safety = [pscustomobject]@{
            method = "out_of_band_tools_list_only"
            readOnly = $true
            noAgentStart = $true
            noTaskMovement = $true
            tunnelTrustedOnlyIfOk = $true
        }
        nextAction = "Run scripts\\Test-OrchTunnelCanary.ps1 -AllowRemote out of band. Do not call this canary through the single-request MCP server."
    }
}

function Get-ActiveFleetPlanTool {
    return Invoke-JsonScript -ScriptPath $ActiveFleetPlanScript -Arguments @("-Root", $Root)
}

function Get-GitHubIssuesCachedTool {
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "issues" 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-GitHubPrStatusCachedTool {
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "prs" 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-GitHubPrDetailTool {
    param([int]$PrNumber)
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "pr_detail" -PrNumber $PrNumber 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-GitHubPrFilesTool {
    param([int]$PrNumber)
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "pr_files" -PrNumber $PrNumber 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-GitHubPrChecksTool {
    param([int]$PrNumber)
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "pr_checks" -PrNumber $PrNumber 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-GitHubPrCommentsTool {
    param([int]$PrNumber)
    $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $GitHubCacheScript -Root $Root -Action "pr_comments" -PrNumber $PrNumber 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "Cache script emitted no output: $GitHubCacheScript" }
    try { $result = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "Cache script emitted invalid JSON: $GitHubCacheScript. $($_.Exception.Message). Output: $text" }
    if ($exitCode -ne 0) { throw "Cache script failed with exit code $($exitCode): $GitHubCacheScript" }
    return $result
}

function Get-OptionalJsonProperty {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    if ($null -eq $Object.PSObject.Properties[$Name]) { return $null }
    return $Object.PSObject.Properties[$Name].Value
}

function New-IbkrUnavailableResult {
    param(
        [string]$ToolName,
        [string]$Message = "IBKR adapter is not configured in this environment.",
        [string]$ErrorCode = "ibkr_unavailable"
    )
    return [pscustomobject]@{
        ok = $false
        error = $ErrorCode
        message = $Message
        retryable = $true
        generatedAt = (Get-Date).ToString("o")
        source = "ibkr"
        tool = $ToolName
        nextAction = "Configure a local IBKR read-only adapter and rerun this tool."
    }
}

function Get-IbkrAdapterSnapshot {
    $defaultPath = Join-Path $Root "status\market-data\ibkr-snapshot.json"
    $configPath = Join-Path $Root "config\ibkr-adapter.local.json"
    $snapshotPath = $defaultPath

    if (Test-Path -LiteralPath $configPath) {
        try {
            $cfg = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json -ErrorAction Stop
            if ($cfg -and $cfg.snapshotPath -and -not [string]::IsNullOrWhiteSpace([string]$cfg.snapshotPath)) {
                $candidate = [string]$cfg.snapshotPath
                if ([System.IO.Path]::IsPathRooted($candidate)) { $snapshotPath = $candidate }
                else { $snapshotPath = Join-Path $Root $candidate }
            }
        }
        catch {}
    }

    if (-not (Test-Path -LiteralPath $snapshotPath)) {
        return $null
    }

    try {
        return (Get-Content -LiteralPath $snapshotPath -Raw | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        return $null
    }
}

function Test-IbkrSnapshotFresh {
    param(
        [object]$Snapshot,
        [int]$MaxQuoteAgeMs = 1500
    )
    if ($null -eq $Snapshot) { return $false }
    $firstQuote = $null
    if ($Snapshot.quotes) {
        $quoteArray = @($Snapshot.quotes)
        if ($quoteArray.Count -gt 0) { $firstQuote = $quoteArray[0] }
    }
    if ($null -ne $firstQuote -and $null -ne $firstQuote.quoteAgeMs) {
        try {
            $quotedAge = [int]$firstQuote.quoteAgeMs
            return $quotedAge -le $MaxQuoteAgeMs
        }
        catch {}
    }

    $generatedAt = $Snapshot.generatedAt
    if ([string]::IsNullOrWhiteSpace([string]$generatedAt)) { return $false }
    try {
        $ts = [DateTimeOffset]::Parse([string]$generatedAt)
        $ageMs = [int](([DateTimeOffset]::UtcNow - $ts.ToUniversalTime()).TotalMilliseconds)
        return $ageMs -le $MaxQuoteAgeMs
    }
    catch {
        return $false
    }
}

function Get-IbkrQuotesTool {
    param([object]$Arguments)
    $symbols = @()
    if ($Arguments -and $Arguments.symbols) { $symbols = @($Arguments.symbols | ForEach-Object { [string]$_ }) }
    if ($symbols.Count -lt 1) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_quotes" -Message "Missing required symbols argument." -ErrorCode "invalid_symbol")
    }
    $maxQuoteAgeMs = 1500
    $requestedMaxAge = Get-OptionalJsonProperty -Object $Arguments -Name "max_quote_age_ms"
    if ($null -ne $requestedMaxAge) {
        try { $maxQuoteAgeMs = [Math]::Max(100, [Math]::Min(10000, [int]$requestedMaxAge)) } catch {}
    }

    $snapshot = Get-IbkrAdapterSnapshot
    if ($null -eq $snapshot) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_quotes")
    }
    if (-not (Test-IbkrSnapshotFresh -Snapshot $snapshot -MaxQuoteAgeMs $maxQuoteAgeMs)) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_quotes" -Message "IBKR snapshot is stale or missing generatedAt." -ErrorCode "stale_data")
    }

    $allQuotes = @()
    if ($snapshot.quotes) { $allQuotes = @($snapshot.quotes) }
    $selected = @($allQuotes | Where-Object { $symbols -contains [string]$_.symbol })
    if ($selected.Count -lt 1) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_quotes" -Message "Requested symbols were not found in IBKR snapshot." -ErrorCode "invalid_symbol")
    }

    $assetClass = "equity"
    $requestedAssetClass = Get-OptionalJsonProperty -Object $Arguments -Name "asset_class"
    if (-not [string]::IsNullOrWhiteSpace([string]$requestedAssetClass)) {
        $assetClass = [string]$requestedAssetClass
    }

    return [pscustomobject]@{
        ok = $true
        generatedAt = [string]$snapshot.generatedAt
        source = "ibkr"
        assetClass = $assetClass
        quotes = $selected
        warnings = @()
        nextAction = "No action required."
    }
}

function Get-IbkrOrderbookTool {
    param([object]$Arguments)
    $symbol = ""
    if ($Arguments -and $Arguments.symbol) { $symbol = [string]$Arguments.symbol }
    if ([string]::IsNullOrWhiteSpace($symbol)) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_orderbook" -Message "Missing required symbol argument." -ErrorCode "invalid_symbol")
    }
    $maxQuoteAgeMs = 1500
    $requestedMaxAge = Get-OptionalJsonProperty -Object $Arguments -Name "max_quote_age_ms"
    if ($null -ne $requestedMaxAge) {
        try { $maxQuoteAgeMs = [Math]::Max(100, [Math]::Min(10000, [int]$requestedMaxAge)) } catch {}
    }

    $snapshot = Get-IbkrAdapterSnapshot
    if ($null -eq $snapshot) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_orderbook")
    }
    if (-not (Test-IbkrSnapshotFresh -Snapshot $snapshot -MaxQuoteAgeMs $maxQuoteAgeMs)) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_orderbook" -Message "IBKR snapshot is stale or missing generatedAt." -ErrorCode "stale_data")
    }

    $books = @()
    if ($snapshot.orderbooks) { $books = @($snapshot.orderbooks) }
    $book = @($books | Where-Object { [string]$_.symbol -eq $symbol } | Select-Object -First 1)
    if ($book.Count -lt 1) {
        return (New-IbkrUnavailableResult -ToolName "get_ibkr_orderbook" -Message "Requested symbol was not found in IBKR orderbook snapshot." -ErrorCode "invalid_symbol")
    }
    return $book[0]
}

function Get-IbkrPositionsTool {
    param([object]$Arguments)
    return (New-IbkrUnavailableResult -ToolName "get_ibkr_positions")
}

function Get-IbkrAccountRiskTool {
    param([object]$Arguments)
    return (New-IbkrUnavailableResult -ToolName "get_ibkr_account_risk")
}

function Get-ConnectorSnapshot {
    param([string]$Venue)
    $safeVenue = ($Venue -replace '[^a-zA-Z0-9\-_]', '').ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($safeVenue)) { return $null }
    $path = Join-Path $Root ("artifacts\market-data\{0}-snapshot.json" -f $safeVenue)
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    try { return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -ErrorAction Stop) } catch { return $null }
}

function Get-QuoteBySymbol {
    param([object]$Snapshot, [string]$Symbol)
    if ($null -eq $Snapshot -or -not $Snapshot.quotes) { return $null }
    $quotes = @($Snapshot.quotes)
    return @($quotes | Where-Object { [string]$_.symbol -eq $Symbol } | Select-Object -First 1)
}

function Rank-SpreadOpportunitiesTool {
    param([object]$Arguments)

    $universeRaw = Get-OptionalJsonProperty -Object $Arguments -Name "universe"
    $venuesRaw = Get-OptionalJsonProperty -Object $Arguments -Name "venues"
    if ($null -eq $universeRaw) { return (New-IbkrUnavailableResult -ToolName "rank_spread_opportunities" -Message "Missing required universe argument." -ErrorCode "invalid_symbol") }
    if ($null -eq $venuesRaw) { return (New-IbkrUnavailableResult -ToolName "rank_spread_opportunities" -Message "Missing required venues argument." -ErrorCode "invalid_symbol") }

    $universe = @($universeRaw | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    $venues = @($venuesRaw | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    if (@($universe).Length -lt 1) { return (New-IbkrUnavailableResult -ToolName "rank_spread_opportunities" -Message "Universe is empty." -ErrorCode "invalid_symbol") }
    if (@($venues).Length -lt 2) { return (New-IbkrUnavailableResult -ToolName "rank_spread_opportunities" -Message "At least two venues are required for spread ranking." -ErrorCode "invalid_symbol") }

    $minNetEdgeBps = 2.5
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "min_net_edge_bps"
    if ($null -ne $v) { try { $minNetEdgeBps = [double]$v } catch {} }
    $feeModel = "conservative"
    $feeModelRaw = Get-OptionalJsonProperty -Object $Arguments -Name "fee_model"
    if (-not [string]::IsNullOrWhiteSpace([string]$feeModelRaw)) { $feeModel = [string]$feeModelRaw }

    $modelFees = 1.1
    $modelSlippage = 0.9
    if ($feeModel -eq "observed") { $modelFees = 0.8; $modelSlippage = 0.7 }
    elseif ($feeModel -eq "stress") { $modelFees = 1.8; $modelSlippage = 1.5 }

    $snapshots = @{}
    foreach ($venue in $venues) {
        if ($venue -eq "ibkr") { $snapshots[$venue] = Get-IbkrAdapterSnapshot }
        else { $snapshots[$venue] = Get-ConnectorSnapshot -Venue $venue }
    }

    $opportunities = @()
    foreach ($symbol in $universe) {
        foreach ($buyVenue in $venues) {
            foreach ($sellVenue in $venues) {
                if ($buyVenue -eq $sellVenue) { continue }
                $buySnap = $snapshots[$buyVenue]
                $sellSnap = $snapshots[$sellVenue]
                $buyQuoteMatch = @(Get-QuoteBySymbol -Snapshot $buySnap -Symbol $symbol)
                $sellQuoteMatch = @(Get-QuoteBySymbol -Snapshot $sellSnap -Symbol $symbol)
                if (@($buyQuoteMatch).Length -lt 1 -or @($sellQuoteMatch).Length -lt 1) { continue }
                $buyQuote = $buyQuoteMatch[0]
                $sellQuote = $sellQuoteMatch[0]
                if ($null -eq $buyQuote.ask -or $null -eq $sellQuote.bid) { continue }

                $buyAsk = [double]$buyQuote.ask
                $sellBid = [double]$sellQuote.bid
                if ($buyAsk -le 0) { continue }
                $grossEdgeBps = (($sellBid - $buyAsk) / $buyAsk) * 10000.0
                $netEdgeBps = $grossEdgeBps - $modelFees - $modelSlippage
                if ($netEdgeBps -lt $minNetEdgeBps) { continue }

                $opportunities += [pscustomobject]@{
                    symbol = $symbol
                    buyVenue = $buyVenue
                    sellVenue = $sellVenue
                    grossEdgeBps = [math]::Round($grossEdgeBps, 4)
                    feesBps = [math]::Round($modelFees, 4)
                    slippageBps = [math]::Round($modelSlippage, 4)
                    netEdgeBps = [math]::Round($netEdgeBps, 4)
                    confidence = 0.70
                    timeToDecayMs = 900
                }
            }
        }
    }

    $ranked = @($opportunities | Sort-Object -Property netEdgeBps -Descending)
    return [pscustomobject]@{
        ok = $true
        generatedAt = (Get-Date).ToString("o")
        source = "spread_engine_paper"
        opportunities = $ranked
        warnings = @()
        nextAction = "No action required."
    }
}

function Simulate-SpreadTradeTool {
    param([object]$Arguments)

    $symbol = [string](Get-OptionalJsonProperty -Object $Arguments -Name "symbol")
    $buyVenue = [string](Get-OptionalJsonProperty -Object $Arguments -Name "buy_venue")
    $sellVenue = [string](Get-OptionalJsonProperty -Object $Arguments -Name "sell_venue")
    $quantityRaw = Get-OptionalJsonProperty -Object $Arguments -Name "quantity"

    if ([string]::IsNullOrWhiteSpace($symbol)) { return (New-IbkrUnavailableResult -ToolName "simulate_spread_trade" -Message "Missing required symbol argument." -ErrorCode "invalid_symbol") }
    if ([string]::IsNullOrWhiteSpace($buyVenue) -or [string]::IsNullOrWhiteSpace($sellVenue)) { return (New-IbkrUnavailableResult -ToolName "simulate_spread_trade" -Message "Missing buy_venue or sell_venue argument." -ErrorCode "invalid_symbol") }
    if ($null -eq $quantityRaw) { return (New-IbkrUnavailableResult -ToolName "simulate_spread_trade" -Message "Missing quantity argument." -ErrorCode "invalid_symbol") }

    $quantity = 0.0
    try { $quantity = [double]$quantityRaw } catch { $quantity = 0.0 }
    if ($quantity -le 0) { return (New-IbkrUnavailableResult -ToolName "simulate_spread_trade" -Message "Quantity must be greater than zero." -ErrorCode "invalid_symbol") }

    $entryDelayMs = 150
    $horizonMs = 30000
    $feeModel = "conservative"
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "entry_delay_ms"; if ($null -ne $v) { try { $entryDelayMs = [int]$v } catch {} }
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "horizon_ms"; if ($null -ne $v) { try { $horizonMs = [int]$v } catch {} }
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "fee_model"; if (-not [string]::IsNullOrWhiteSpace([string]$v)) { $feeModel = [string]$v }

    $buySnap = $(if ($buyVenue -eq "ibkr") { Get-IbkrAdapterSnapshot } else { Get-ConnectorSnapshot -Venue $buyVenue })
    $sellSnap = $(if ($sellVenue -eq "ibkr") { Get-IbkrAdapterSnapshot } else { Get-ConnectorSnapshot -Venue $sellVenue })
    $buyQuoteMatch = @(Get-QuoteBySymbol -Snapshot $buySnap -Symbol $symbol)
    $sellQuoteMatch = @(Get-QuoteBySymbol -Snapshot $sellSnap -Symbol $symbol)
    if (@($buyQuoteMatch).Length -lt 1 -or @($sellQuoteMatch).Length -lt 1) {
        return (New-IbkrUnavailableResult -ToolName "simulate_spread_trade" -Message "Missing quote(s) for requested symbol/venues in snapshot fixtures." -ErrorCode "invalid_symbol")
    }
    $buyQuote = $buyQuoteMatch[0]
    $sellQuote = $sellQuoteMatch[0]
    if ($null -eq $buyQuote.ask -or $null -eq $sellQuote.bid) {
        return (New-IbkrUnavailableResult -ToolName "simulate_spread_trade" -Message "Required ask/bid fields are missing in fixture quotes." -ErrorCode "invalid_symbol")
    }

    $entryMid = ([double]$buyQuote.ask + [double]$sellQuote.bid) / 2.0
    $exitMid = $entryMid + (($entryMid * 0.00005)) # +0.5 bps simulated drift
    $grossPnl = (([double]$sellQuote.bid - [double]$buyQuote.ask) * $quantity)

    $feeBps = 1.1
    $slippageBps = 0.9
    if ($feeModel -eq "observed") { $feeBps = 0.8; $slippageBps = 0.7 }
    elseif ($feeModel -eq "stress") { $feeBps = 1.8; $slippageBps = 1.5 }

    $notional = [math]::Abs($entryMid * $quantity)
    $fees = $notional * ($feeBps / 10000.0)
    $slippage = $notional * ($slippageBps / 10000.0)
    $netPnl = $grossPnl - $fees - $slippage
    $netEdgeBps = $(if ($notional -gt 0) { ($netPnl / $notional) * 10000.0 } else { 0.0 })

    return [pscustomobject]@{
        ok = $true
        generatedAt = (Get-Date).ToString("o")
        source = "spread_engine_paper"
        simulation = [pscustomobject]@{
            symbol = $symbol
            buyVenue = $buyVenue
            sellVenue = $sellVenue
            quantity = $quantity
            entryMid = [math]::Round($entryMid, 6)
            exitMid = [math]::Round($exitMid, 6)
            grossPnl = [math]::Round($grossPnl, 6)
            fees = [math]::Round($fees, 6)
            slippage = [math]::Round($slippage, 6)
            netPnl = [math]::Round($netPnl, 6)
            netEdgeBps = [math]::Round($netEdgeBps, 6)
            maxAdverseBps = 1.3
            durationMs = [Math]::Max(100, $horizonMs + $entryDelayMs)
        }
        warnings = @()
        nextAction = "No action required."
    }
}

function Get-SpreadExecutionReadinessTool {
    param([object]$Arguments)

    $universe = @("SPY", "QQQ")
    $u = Get-OptionalJsonProperty -Object $Arguments -Name "universe"
    if ($null -ne $u) {
        $parsed = @($u | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
        if ($parsed.Count -gt 0) { $universe = $parsed }
    }

    $venues = @("ibkr", "venueb")
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "venues"
    if ($null -ne $v) {
        $parsed = @($v | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
        if ($parsed.Count -gt 1) { $venues = $parsed }
    }

    $maxQuoteAgeMs = 1500
    $ageArg = Get-OptionalJsonProperty -Object $Arguments -Name "max_quote_age_ms"
    if ($null -ne $ageArg) { try { $maxQuoteAgeMs = [Math]::Max(100, [Math]::Min(10000, [int]$ageArg)) } catch {} }

    $blockers = @()
    $venueChecks = @()
    $supportsLive = $false
    $freshVenueCount = 0

    foreach ($venue in $venues) {
        $snapshot = $(if ($venue -eq "ibkr") { Get-IbkrAdapterSnapshot } else { Get-ConnectorSnapshot -Venue $venue })
        $hasSnapshot = ($null -ne $snapshot)
        $fresh = $false
        if ($hasSnapshot) { $fresh = Test-IbkrSnapshotFresh -Snapshot $snapshot -MaxQuoteAgeMs $maxQuoteAgeMs }
        if ($fresh) { $freshVenueCount++ }

        $presentCount = 0
        if ($hasSnapshot -and $snapshot.quotes) {
            $symbols = @($snapshot.quotes | ForEach-Object { [string]$_.symbol })
            $presentCount = @($universe | Where-Object { $symbols -contains $_ }).Count
        }
        if (-not $hasSnapshot) { $blockers += ("missing_snapshot:{0}" -f $venue) }
        elseif (-not $fresh) { $blockers += ("stale_snapshot:{0}" -f $venue) }
        elseif ($presentCount -lt 1) { $blockers += ("missing_universe_quotes:{0}" -f $venue) }

        if ($venue -eq "ibkr") { $supportsLive = $supportsLive -or $hasSnapshot }
        $venueChecks += [pscustomobject]@{
            venue = $venue
            hasSnapshot = $hasSnapshot
            fresh = $fresh
            universeCoverageCount = $presentCount
            supportsExecutionPath = ($venue -eq "ibkr")
        }
    }

    $hasPair = ($freshVenueCount -ge 2)
    if (-not $hasPair) { $blockers += "insufficient_fresh_venues" }
    if (-not $supportsLive) { $blockers += "no_execution_connector_path" }
    $blockers = @($blockers | Select-Object -Unique)

    $ready = ($blockers.Count -eq 0)
    $status = $(if ($ready) { "ready" } else { "held" })
    return [pscustomobject]@{
        ok = $true
        status = $status
        ready = $ready
        generatedAt = (Get-Date).ToString("o")
        source = "spread_execution_gate"
        checks = [pscustomobject]@{
            universe = $universe
            venues = $venues
            maxQuoteAgeMs = $maxQuoteAgeMs
            freshVenueCount = $freshVenueCount
            requiresFreshVenuePair = $true
            requiresExecutionConnectorPath = $true
        }
        venueChecks = $venueChecks
        blockers = $blockers
        deploymentSuccessClaimAllowed = $ready
        nextAction = $(if ($ready) { "Proceed with guarded paper-to-live promotion checks." } else { "Hold live spread execution; resolve blockers and rerun get_spread_execution_readiness." })
    }
}

function Get-SpreadProfitabilitySnapshotTool {
    param([object]$Arguments)

    $universe = @("SPY", "QQQ")
    $u = Get-OptionalJsonProperty -Object $Arguments -Name "universe"
    if ($null -ne $u) {
        $parsed = @($u | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
        if ($parsed.Count -gt 0) { $universe = $parsed }
    }
    $venues = @("ibkr", "venueb")
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "venues"
    if ($null -ne $v) {
        $parsed = @($v | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
        if ($parsed.Count -gt 1) { $venues = $parsed }
    }
    $quantity = 100.0
    $q = Get-OptionalJsonProperty -Object $Arguments -Name "quantity"
    if ($null -ne $q) { try { $quantity = [double]$q } catch {} }
    if ($quantity -le 0) { $quantity = 100.0 }

    $rank = Rank-SpreadOpportunitiesTool -Arguments ([pscustomobject]@{
        universe = $universe
        venues = $venues
        min_net_edge_bps = 0
        fee_model = "conservative"
    })
    $gate = Get-SpreadExecutionReadinessTool -Arguments ([pscustomobject]@{
        universe = $universe
        venues = $venues
    })

    $top = @()
    if ($rank.ok -eq $true -and $rank.opportunities) {
        $top = @($rank.opportunities | Select-Object -First 5)
    }

    $simulations = @()
    foreach ($op in $top) {
        $sim = Simulate-SpreadTradeTool -Arguments ([pscustomobject]@{
            symbol = [string]$op.symbol
            buy_venue = [string]$op.buyVenue
            sell_venue = [string]$op.sellVenue
            quantity = $quantity
            fee_model = "conservative"
        })
        if ($sim.ok -eq $true -and $sim.simulation) {
            $simulations += $sim.simulation
        }
    }

    $best = @($simulations | Sort-Object -Property netPnl -Descending | Select-Object -First 1)
    $hasEvidence = ($simulations.Count -gt 0)
    $bestNetPnl = $(if ($best.Count -gt 0) { [double]$best[0].netPnl } else { 0.0 })
    $profitabilityProvenNow = ($hasEvidence -and $bestNetPnl -gt 0 -and $gate.ready -eq $true)
    $claim = $(if ($profitabilityProvenNow) { "provisional_paper_positive" } else { "not_proven" })

    return [pscustomobject]@{
        ok = $true
        generatedAt = (Get-Date).ToString("o")
        source = "spread_profitability_snapshot"
        universe = $universe
        venues = $venues
        quantity = $quantity
        readiness = $gate
        opportunitiesConsidered = @($rank.opportunities).Count
        simulationsRun = $simulations.Count
        topOpportunities = $top
        topSimulations = $simulations
        profitability = [pscustomobject]@{
            claim = $claim
            profitabilityProvenNow = $profitabilityProvenNow
            bestNetPnl = [math]::Round($bestNetPnl, 6)
            confidence = $(if ($profitabilityProvenNow) { 0.55 } else { 0.0 })
            truthStatement = $(if ($profitabilityProvenNow) { "Paper-only snapshot indicates positive simulated spread PnL with readiness gate open. Live profitability is still unverified." } else { "Profitability is not proven from current evidence. Keep paper mode and improve connector freshness/coverage." })
        }
        nextAction = $(if ($profitabilityProvenNow) { "Run guarded live micro-size execution experiment with strict risk limits." } else { "Resolve readiness blockers and expand fresh venue coverage before any live execution claim." })
    }
}

function Plan-SpreadLiveMicroExperimentTool {
    param([object]$Arguments)

    $snapshot = Get-SpreadProfitabilitySnapshotTool -Arguments $Arguments
    $maxLossUsd = 15.0
    $m = Get-OptionalJsonProperty -Object $Arguments -Name "max_loss_usd"
    if ($null -ne $m) { try { $maxLossUsd = [Math]::Max(1.0, [double]$m) } catch {} }
    $maxNotionalUsd = 1500.0
    $n = Get-OptionalJsonProperty -Object $Arguments -Name "max_notional_usd"
    if ($null -ne $n) { try { $maxNotionalUsd = [Math]::Max(100.0, [double]$n) } catch {} }

    $canRun = ($snapshot.profitability.profitabilityProvenNow -eq $true -and $snapshot.readiness.ready -eq $true)
    $status = $(if ($canRun) { "ready_to_execute_guarded" } else { "hold" })

    $steps = @(
        "Verify connector auth/session health for buy and sell venues.",
        "Place micro-size paired orders with hard timeout cancel (no averaging).",
        "Abort immediately if realized slippage exceeds modeled slippage by > 1.0 bps.",
        "Stop run if cumulative realized PnL <= -max_loss_usd.",
        "Record realized edge, fill latency, and reject reasons for post-trade truth audit."
    )

    return [pscustomobject]@{
        ok = $true
        generatedAt = (Get-Date).ToString("o")
        source = "spread_live_micro_experiment_planner"
        status = $status
        canExecuteNow = $canRun
        guardrails = [pscustomobject]@{
            maxLossUsd = [math]::Round($maxLossUsd, 2)
            maxNotionalUsd = [math]::Round($maxNotionalUsd, 2)
            requirePairedExecution = $true
            cancelOnTimeoutMs = 1200
            haltOnSlippageOvershootBps = 1.0
        }
        evidence = [pscustomobject]@{
            profitabilityClaim = [string]$snapshot.profitability.claim
            profitabilityProvenNow = [bool]$snapshot.profitability.profitabilityProvenNow
            readinessStatus = [string]$snapshot.readiness.status
            blockers = @($snapshot.readiness.blockers)
        }
        executionPlan = $steps
        nextAction = $(if ($canRun) { "Execute one guarded micro-size live trial and compare realized vs simulated edge." } else { "Hold live execution; resolve readiness/profitability blockers and rerun plan_spread_live_micro_experiment." })
    }
}

function Create-SpreadExperimentBriefTool {
    param([object]$Arguments)

    $plan = Plan-SpreadLiveMicroExperimentTool -Arguments $Arguments
    $snapshot = Get-SpreadProfitabilitySnapshotTool -Arguments $Arguments
    $generatedAt = (Get-Date).ToString("o")

    $title = "Spread Live Micro-Experiment Brief"
    $statusLine = "Status: {0}" -f [string]$plan.status
    $claimLine = "Profitability Claim: {0}" -f [string]$snapshot.profitability.claim
    $truthLine = "Truth: {0}" -f [string]$snapshot.profitability.truthStatement

    $criteria = @(
        "Readiness status is ready and blockers list is empty.",
        "At least one live micro trade pair completes within timeout.",
        "Realized slippage overshoot stays <= configured threshold.",
        "Cumulative realized PnL remains above -maxLossUsd.",
        "Post-trade report contains realized vs simulated net edge delta."
    )
    $rollback = @(
        "Any venue auth/session health check fails.",
        "Paired execution cannot complete within timeout window.",
        "Cumulative realized PnL breaches max loss cap.",
        "Observed slippage overshoot exceeds threshold."
    )

    $body = @(
        ("# {0}" -f $title),
        "",
        ("GeneratedAt: {0}" -f $generatedAt),
        $statusLine,
        $claimLine,
        $truthLine,
        "",
        "## Guardrails",
        ("- maxLossUsd: {0}" -f $plan.guardrails.maxLossUsd),
        ("- maxNotionalUsd: {0}" -f $plan.guardrails.maxNotionalUsd),
        ("- cancelOnTimeoutMs: {0}" -f $plan.guardrails.cancelOnTimeoutMs),
        ("- haltOnSlippageOvershootBps: {0}" -f $plan.guardrails.haltOnSlippageOvershootBps),
        "",
        "## Acceptance Criteria",
        ("- " + ($criteria -join "`n- ")),
        "",
        "## Rollback Triggers",
        ("- " + ($rollback -join "`n- ")),
        "",
        "## Next Action",
        ("- {0}" -f [string]$plan.nextAction)
    ) -join "`n"

    return [pscustomobject]@{
        ok = $true
        generatedAt = $generatedAt
        source = "spread_experiment_brief"
        status = [string]$plan.status
        canExecuteNow = [bool]$plan.canExecuteNow
        title = $title
        bodyMarkdown = $body
        readiness = $plan.evidence
        guardrails = $plan.guardrails
        profitability = $snapshot.profitability
        nextAction = "Use bodyMarkdown to create or update a GitHub issue/PR task for the live micro-experiment."
    }
}

function Get-LiveSteeringStateTool {
    param([object]$Arguments)
    $snapshot = Get-SpreadProfitabilitySnapshotTool -Arguments $Arguments
    $plan = Plan-SpreadLiveMicroExperimentTool -Arguments $Arguments
    return [pscustomobject]@{
        ok = $true
        generatedAt = (Get-Date).ToString("o")
        source = "live_spread_steering_state"
        readinessStatus = [string]$snapshot.readiness.status
        profitabilityClaim = [string]$snapshot.profitability.claim
        profitabilityProvenNow = [bool]$snapshot.profitability.profitabilityProvenNow
        bestNetPnl = [double]$snapshot.profitability.bestNetPnl
        blockers = @($snapshot.readiness.blockers)
        recommendedMode = $(if ($plan.canExecuteNow) { "execute_guarded" } else { "hold" })
    }
}

function Steer-LiveSpreadTradeTool {
    param([object]$Arguments)

    $symbol = [string](Get-OptionalJsonProperty -Object $Arguments -Name "symbol")
    if ([string]::IsNullOrWhiteSpace($symbol)) { $symbol = "SPY" }
    $buyVenue = [string](Get-OptionalJsonProperty -Object $Arguments -Name "buy_venue")
    if ([string]::IsNullOrWhiteSpace($buyVenue)) { $buyVenue = "ibkr" }
    $sellVenue = [string](Get-OptionalJsonProperty -Object $Arguments -Name "sell_venue")
    if ([string]::IsNullOrWhiteSpace($sellVenue)) { $sellVenue = "venueb" }

    $realizedPnl = 0.0
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "realized_pnl_usd"; if ($null -ne $v) { try { $realizedPnl = [double]$v } catch {} }
    $slippageOvershootBps = 0.0
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "slippage_overshoot_bps"; if ($null -ne $v) { try { $slippageOvershootBps = [double]$v } catch {} }
    $fillLatencyMs = 0
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "fill_latency_ms"; if ($null -ne $v) { try { $fillLatencyMs = [int]$v } catch {} }

    $lossFloorUsd = 0.0
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "loss_floor_usd"; if ($null -ne $v) { try { $lossFloorUsd = [double]$v } catch {} }
    $exitEdgeFloorBps = 0.2
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "exit_edge_floor_bps"; if ($null -ne $v) { try { $exitEdgeFloorBps = [double]$v } catch {} }
    $maxSlippageOvershootBps = 2.0
    $v = Get-OptionalJsonProperty -Object $Arguments -Name "max_slippage_overshoot_bps"; if ($null -ne $v) { try { $maxSlippageOvershootBps = [double]$v } catch {} }

    $sim = Simulate-SpreadTradeTool -Arguments ([pscustomobject]@{
        symbol = $symbol
        buy_venue = $buyVenue
        sell_venue = $sellVenue
        quantity = 100
        fee_model = "conservative"
    })
    $edgeBps = 0.0
    if ($sim.ok -eq $true -and $sim.simulation) { $edgeBps = [double]$sim.simulation.netEdgeBps }

    $state = Get-LiveSteeringStateTool -Arguments $Arguments

    $action = "hold"
    $reasons = @()
    if ($realizedPnl -lt $lossFloorUsd) {
        $action = "kill_switch"
        $reasons += ("realized_pnl_breached_floor({0} < {1})" -f $realizedPnl, $lossFloorUsd)
    }
    elseif ($slippageOvershootBps -ge $maxSlippageOvershootBps) {
        $action = "exit_now"
        $reasons += ("slippage_overshoot({0} >= {1})" -f $slippageOvershootBps, $maxSlippageOvershootBps)
    }
    elseif ($edgeBps -lt $exitEdgeFloorBps) {
        $action = "exit_now"
        $reasons += ("edge_collapse({0} < {1})" -f ([math]::Round($edgeBps, 4)), $exitEdgeFloorBps)
    }
    elseif ($state.recommendedMode -ne "execute_guarded") {
        $action = "hold"
        $reasons += "readiness_not_execute_guarded"
    }
    elseif ($fillLatencyMs -ge 1500) {
        $action = "reduce"
        $reasons += ("high_fill_latency_ms({0})" -f $fillLatencyMs)
    }
    else {
        $action = "enter"
        $reasons += "edge_positive_and_readiness_ok"
    }

    return [pscustomobject]@{
        ok = $true
        generatedAt = (Get-Date).ToString("o")
        source = "live_spread_steering"
        action = $action
        symbol = $symbol
        buyVenue = $buyVenue
        sellVenue = $sellVenue
        thresholds = [pscustomobject]@{
            lossFloorUsd = $lossFloorUsd
            exitEdgeFloorBps = $exitEdgeFloorBps
            maxSlippageOvershootBps = $maxSlippageOvershootBps
            reduceOnFillLatencyMs = 1500
        }
        telemetry = [pscustomobject]@{
            realizedPnlUsd = $realizedPnl
            slippageOvershootBps = $slippageOvershootBps
            fillLatencyMs = $fillLatencyMs
            simulatedNetEdgeBps = [math]::Round($edgeBps, 6)
        }
        state = $state
        reasons = $reasons
        nextAction = "Apply action immediately and repoll steer_live_spread_trade within 250-500ms."
    }
}

function Get-SpreadOperatorPacketTool {
    param([object]$Arguments)
    $state = Get-LiveSteeringStateTool -Arguments $Arguments
    $steer = Steer-LiveSpreadTradeTool -Arguments $Arguments
    $now = (Get-Date).ToString("o")
    $summary = @(
        ("GeneratedAt: {0}" -f $now),
        ("Action: {0}" -f [string]$steer.action),
        ("Mode: {0}" -f [string]$state.recommendedMode),
        ("Readiness: {0}" -f [string]$state.readinessStatus),
        ("ProfitabilityClaim: {0}" -f [string]$state.profitabilityClaim),
        ("RealizedPnlUsd: {0}" -f [string]$steer.telemetry.realizedPnlUsd),
        ("SimulatedNetEdgeBps: {0}" -f [string]$steer.telemetry.simulatedNetEdgeBps),
        ("Reason: {0}" -f @($steer.reasons)[0])
    ) -join "`n"

    return [pscustomobject]@{
        ok = $true
        generatedAt = $now
        source = "spread_operator_packet"
        action = $steer.action
        decision = [pscustomobject]@{
            reasons = @($steer.reasons)
            thresholds = $steer.thresholds
            telemetry = $steer.telemetry
        }
        state = $state
        githubCommentMarkdown = @(
            "## Live Spread Steering Update",
            "",
            '```text',
            $summary,
            '```',
            "",
            ("NextAction: {0}" -f [string]$steer.nextAction)
        ) -join "`n"
    }
}
function Update-GitHubIssueCommentTool {
    param([object]$Arguments)

    $commentId = Get-OptionalJsonProperty -Object $Arguments -Name "comment_id"
    if ($null -eq $commentId) { throw "Missing required argument: comment_id" }

    $args = @("-Root", $Root, "-CommentId", [string]$commentId)

    $body = Get-OptionalJsonProperty -Object $Arguments -Name "body"
    $bodyPath = Get-OptionalJsonProperty -Object $Arguments -Name "body_path"
    $expectedContains = Get-OptionalJsonProperty -Object $Arguments -Name "expected_contains"
    $maxBodyLength = Get-OptionalJsonProperty -Object $Arguments -Name "max_body_length"
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"

    if (-not [string]::IsNullOrWhiteSpace([string]$body)) { $args += @("-Body", [string]$body) }
    if (-not [string]::IsNullOrWhiteSpace([string]$bodyPath)) { $args += @("-BodyPath", [string]$bodyPath) }
    if (-not [string]::IsNullOrWhiteSpace([string]$expectedContains)) { $args += @("-ExpectedContains", [string]$expectedContains) }
    if ($null -ne $maxBodyLength) { $args += @("-MaxBodyLength", [string]$maxBodyLength) }
    if ($true -eq [bool]$dryRun) { $args += "-DryRun" }

    return Invoke-JsonScript -ScriptPath $GitHubIssueCommentScript -Arguments $args
}

function Get-GameMakerProjectInfoTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerProjectInfoScript -Arguments $args
}

function Get-GameMakerCompilerErrorsTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerCompilerErrorsScript -Arguments $args
}

function Get-GameMakerSpriteAssetStatusTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerSpriteStatusScript -Arguments $args
}

function Get-GameMakerRoomEditorStatusTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerRoomStatusScript -Arguments $args
}

function Get-GameMakerBuildStatusTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.project) { $args += @("-ProjectName", [string]$Arguments.project) }
    return Invoke-JsonScript -ScriptPath $GameMakerBuildStatusScript -Arguments $args
}

function Invoke-SyncRepositoryTool {
    param([object]$Arguments)
    $args = @("-Root", $Root)
    if ($Arguments -and $Arguments.remote) { $args += @("-Remote", [string]$Arguments.remote) }
    if ($Arguments -and $Arguments.branch) { $args += @("-Branch", [string]$Arguments.branch) }
    if ($Arguments -and $Arguments.dry_run) { $args += "-DryRun" }
    if ($Arguments -and $Arguments.plan_only) { $args += "-PlanOnly" }
    if ($Arguments -and $Arguments.allow_dirty) { $args += "-AllowDirty" }
    return Invoke-JsonScript -ScriptPath $RepoSyncScript -Arguments $args
}

function Invoke-TaskActionTool {
    param([string]$Action, [object]$Arguments)
    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.task_path)) { throw "Missing required argument: task_path" }
    $args = @("-Root", $Root, "-Action", $Action, "-TaskPath", [string]$Arguments.task_path)
    if ($Arguments.reason) { $args += @("-Reason", [string]$Arguments.reason) }
    if ($Arguments.dry_run) { $args += "-DryRun" }
    if ($Arguments.allow_dirty) { $args += "-AllowDirty" }
    return Invoke-JsonScript -ScriptPath $TaskActionScript -Arguments $args
}

function Invoke-AgentActionTool {
    param([string]$Action, [object]$Arguments)
    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.slot)) { throw "Missing required argument: slot" }
    $args = @("-Root", $Root, "-Action", $Action, "-SlotName", [string]$Arguments.slot)
    if ($Arguments.dry_run) { $args += "-DryRun" }
    return Invoke-JsonScript -ScriptPath $AgentActionScript -Arguments $args
}

function Invoke-SafePowerShellRunnerTool {
    param([object]$Arguments)

    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.script_name)) { throw "Missing required argument: script_name" }
    $scriptName = [string]$Arguments.script_name

    $args = @("-Root", $Root, "-ScriptName", $scriptName)

    $argumentJson = Get-OptionalJsonProperty -Object $Arguments -Name "argument_json"
    $argumentJsonBase64 = Get-OptionalJsonProperty -Object $Arguments -Name "argument_json_base64"
    $rawArguments = Get-OptionalJsonProperty -Object $Arguments -Name "arguments"
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"
    $planOnly = Get-OptionalJsonProperty -Object $Arguments -Name "plan_only"
    $timeoutSeconds = Get-OptionalJsonProperty -Object $Arguments -Name "timeout_seconds"

    if (-not [string]::IsNullOrWhiteSpace([string]$argumentJson)) { $args += @("-ArgumentJson", [string]$argumentJson) }
    elseif (-not [string]::IsNullOrWhiteSpace([string]$argumentJsonBase64)) { $args += @("-ArgumentJsonBase64", [string]$argumentJsonBase64) }
    elseif ($null -ne $rawArguments) { $args += @("-ArgumentJson", ($rawArguments | ConvertTo-Json -Depth 80 -Compress)) }
    if ($true -eq [bool]$dryRun) { $args += "-DryRun" }
    if ($true -eq [bool]$planOnly) { $args += "-PlanOnly" }
    if ($null -ne $timeoutSeconds) { $args += @("-TimeoutSeconds", [string]$timeoutSeconds) }

    return Invoke-JsonScript -ScriptPath $SafePowerShellRunnerScript -Arguments $args
}

function Restart-McpServerTool {
    param([object]$Arguments)

    if ($null -eq $Arguments) { $Arguments = [pscustomobject]@{} }
    $reason = Get-OptionalJsonProperty -Object $Arguments -Name "reason"
    if ([string]::IsNullOrWhiteSpace([string]$reason)) { throw "Missing required argument: reason" }

    $args = @("-Root", $Root, "-Reason", [string]$reason)
    $requestedPort = Get-OptionalJsonProperty -Object $Arguments -Name "port"
    $requestedNoAuth = Get-OptionalJsonProperty -Object $Arguments -Name "no_auth"
    $requestedDelay = Get-OptionalJsonProperty -Object $Arguments -Name "delay_seconds"
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"

    if ($null -ne $requestedPort) { $args += @("-Port", [string]$requestedPort) } else { $args += @("-Port", [string]$Port) }
    if ($null -ne $requestedNoAuth) { $args += @("-NoAuth", [string]([bool]$requestedNoAuth)) } else { $args += @("-NoAuth", [string]([bool]$NoAuth)) }
    if ($null -ne $requestedDelay) { $args += @("-DelaySeconds", [string]$requestedDelay) }
    if ($null -eq $dryRun -or $true -eq [bool]$dryRun) { $args += "-DryRun" }

    return Invoke-JsonScript -ScriptPath $McpRestartScript -Arguments $args
}

function Run-ServiceSupervisorTool {
    param([object]$Arguments)

    if ($null -eq $Arguments) { $Arguments = [pscustomobject]@{} }
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"
    $args = @("-Root", $Root, "-Once")
    if ($null -eq $dryRun -or $true -eq [bool]$dryRun) { $args += "-DryRun" }
    return Invoke-JsonScript -ScriptPath $ServiceSupervisorScript -Arguments $args
}

function Get-McpFeatureOverviewTool {
    $toolNames = @((Get-ToolsList).tools | ForEach-Object { [string]$_.name })
    return [pscustomobject]@{
        generatedAt = (Get-Date).ToString("o")
        server = [pscustomobject]@{
            port = $Port
            noAuth = [bool]$NoAuth
            healthUrl = "http://127.0.0.1:$Port/health"
            mcpUrl = "http://127.0.0.1:$Port/mcp"
        }
        groups = [pscustomobject]@{
            status = @("get_agent_status", "get_queue_summary", "get_recent_failures", "get_latest_agent_logs", "get_mcp_capability_status", "get_mcp_feature_overview")
            taskOps = @("create_queue_task", "requeue_task", "fail_task", "complete_task")
            agentOps = @("start_agent", "rerun_agent")
            gitAndGitHubOps = @(
                "sync_repository",
                "get_github_issues_cached",
                "get_github_pr_status_cached",
                "get_github_pr_detail",
                "get_github_pr_files",
                "get_github_pr_checks",
                "get_github_pr_comments",
                "update_github_issue_comment",
                "get_git_status_summary",
                "get_worktree_risk_summary",
                "create_branch",
                "stage_files",
                "commit_staged_changes",
                "push_current_branch",
                "open_pr"
            )
            powershellOps = @("run_safe_powershell", "propose_powershell_patch", "validate_powershell_patch", "promote_powershell_patch")
            serviceOps = @("restart_mcp_server", "run_service_supervisor", "get_tunnel_canary_status", "get_active_fleet_plan")
            gameMakerOps = @("get_gamemaker_project_info", "get_gamemaker_compiler_errors", "get_sprite_asset_status", "get_room_editor_status", "get_game_build_status")
            marketData = @("get_ibkr_quotes", "get_ibkr_orderbook", "get_ibkr_positions", "get_ibkr_account_risk", "rank_spread_opportunities", "simulate_spread_trade", "get_spread_execution_readiness", "get_spread_profitability_snapshot", "plan_spread_live_micro_experiment", "create_spread_experiment_brief", "get_live_steering_state", "steer_live_spread_trade", "get_spread_operator_packet")
        }
        availableTools = $toolNames
        missingOpsGaps = @(
            "hold_task",
            "resume_held_task",
            "annotate_task",
            "add_github_pr_comment",
            "update_github_pr_metadata",
            "compare_github_refs",
            "get_github_file",
            "get_github_pr_patch"
        )
        safety = [pscustomobject]@{
            arbitraryShell = $false
            safePowerShellAllowlistOnly = $true
            mcpRestartSchedulesDetachedWorker = $true
            coldStartScriptExposed = $false
        }
    }
}

function Invoke-CreateQueueTaskTool {
    param([object]$Arguments)

    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.title)) { throw "Missing required argument: title" }
    $args = @("-Root", $Root, "-Title", [string]$Arguments.title)

    $body = Get-OptionalJsonProperty -Object $Arguments -Name "body"
    $reason = Get-OptionalJsonProperty -Object $Arguments -Name "reason"
    $priority = Get-OptionalJsonProperty -Object $Arguments -Name "priority"
    $owner = Get-OptionalJsonProperty -Object $Arguments -Name "owner"
    $blockedBy = Get-OptionalJsonProperty -Object $Arguments -Name "blocked_by"
    if ($null -eq $blockedBy) { $blockedBy = Get-OptionalJsonProperty -Object $Arguments -Name "blockedBy" }
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"

    if (-not [string]::IsNullOrWhiteSpace([string]$body)) { $args += @("-Body", [string]$body) }
    if (-not [string]::IsNullOrWhiteSpace([string]$reason)) { $args += @("-Reason", [string]$reason) }
    if (-not [string]::IsNullOrWhiteSpace([string]$priority)) { $args += @("-Priority", [string]$priority) }
    if (-not [string]::IsNullOrWhiteSpace([string]$owner)) { $args += @("-Owner", [string]$owner) }
    if (-not [string]::IsNullOrWhiteSpace([string]$blockedBy)) { $args += @("-BlockedBy", [string]$blockedBy) }
    if ($null -eq $dryRun -or $true -eq $dryRun -or "true" -eq [string]$dryRun) { $args += "-DryRun" }

    return Invoke-JsonScript -ScriptPath $QueueTaskCreateScript -Arguments $args
}

function New-ToolTextResult {
    param([object]$Value)
    return [pscustomobject]@{ content = @([pscustomobject]@{ type = "text"; text = ($Value | ConvertTo-Json -Depth 80) }) }
}

function New-ObjectSchema {
    param([object]$Properties, [string[]]$Required = @())
    return [pscustomobject]@{ type = "object"; properties = $Properties; required = $Required; additionalProperties = $false }
}

function Get-ToolsList {
    $empty = New-ObjectSchema -Properties ([pscustomobject]@{})
    $taskProperties = [pscustomobject]@{ task_path = [pscustomobject]@{ type = "string" }; reason = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; allow_dirty = [pscustomobject]@{ type = "boolean"; default = $false } }
    $agentProperties = [pscustomobject]@{ slot = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false } }
    $commentProperties = [pscustomobject]@{ comment_id = [pscustomobject]@{ type = "integer" }; body = [pscustomobject]@{ type = "string" }; body_path = [pscustomobject]@{ type = "string" }; expected_contains = [pscustomobject]@{ type = "string" }; max_body_length = [pscustomobject]@{ type = "integer"; minimum = 1; maximum = 65000; default = 65000 }; dry_run = [pscustomobject]@{ type = "boolean"; default = $true } }
    $patchProperties = [pscustomobject]@{ patch_id = [pscustomobject]@{ type = "string" }; target_path = [pscustomobject]@{ type = "string" }; content_path = [pscustomobject]@{ type = "string" }; reason = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $true } }
    $restartProperties = [pscustomobject]@{ reason = [pscustomobject]@{ type = "string" }; port = [pscustomobject]@{ type = "integer"; minimum = 1; maximum = 65535; default = 8787 }; no_auth = [pscustomobject]@{ type = "boolean"; default = $true }; delay_seconds = [pscustomobject]@{ type = "integer"; minimum = 0; maximum = 60; default = 2 }; dry_run = [pscustomobject]@{ type = "boolean"; default = $true } }
    $supervisorProperties = [pscustomobject]@{ dry_run = [pscustomobject]@{ type = "boolean"; default = $true } }
    $ibkrQuotesProperties = [pscustomobject]@{
        symbols = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 1; maxItems = 200 }
        asset_class = [pscustomobject]@{ type = "string"; enum = @("equity", "option", "future", "forex", "index"); default = "equity" }
        include_greeks = [pscustomobject]@{ type = "boolean"; default = $false }
        max_quote_age_ms = [pscustomobject]@{ type = "integer"; minimum = 100; maximum = 10000; default = 1500 }
    }
    $ibkrOrderbookProperties = [pscustomobject]@{
        symbol = [pscustomobject]@{ type = "string" }
        asset_class = [pscustomobject]@{ type = "string"; enum = @("equity", "future", "forex"); default = "equity" }
        depth_levels = [pscustomobject]@{ type = "integer"; minimum = 1; maximum = 20; default = 10 }
        max_quote_age_ms = [pscustomobject]@{ type = "integer"; minimum = 100; maximum = 10000; default = 1500 }
    }
    $ibkrPositionsProperties = [pscustomobject]@{
        account = [pscustomobject]@{ type = "string" }
        include_unrealized = [pscustomobject]@{ type = "boolean"; default = $true }
    }
    $ibkrRiskProperties = [pscustomobject]@{
        account = [pscustomobject]@{ type = "string" }
    }
    $spreadRankProperties = [pscustomobject]@{
        universe = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 1; maxItems = 500 }
        venues = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 2 }
        min_net_edge_bps = [pscustomobject]@{ type = "number"; minimum = 0; default = 2.5 }
        max_quote_age_ms = [pscustomobject]@{ type = "integer"; minimum = 100; maximum = 5000; default = 1500 }
        fee_model = [pscustomobject]@{ type = "string"; enum = @("conservative", "observed", "stress"); default = "conservative" }
    }
    $spreadSimProperties = [pscustomobject]@{
        symbol = [pscustomobject]@{ type = "string" }
        buy_venue = [pscustomobject]@{ type = "string" }
        sell_venue = [pscustomobject]@{ type = "string" }
        quantity = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0 }
        entry_delay_ms = [pscustomobject]@{ type = "integer"; minimum = 0; maximum = 2000; default = 150 }
        exit_rule = [pscustomobject]@{ type = "string"; enum = @("time", "target_edge", "stop_loss"); default = "time" }
        horizon_ms = [pscustomobject]@{ type = "integer"; minimum = 100; maximum = 600000; default = 30000 }
        fee_model = [pscustomobject]@{ type = "string"; enum = @("conservative", "observed", "stress"); default = "conservative" }
    }
    $spreadReadinessProperties = [pscustomobject]@{
        universe = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 1; maxItems = 500 }
        venues = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 2 }
        max_quote_age_ms = [pscustomobject]@{ type = "integer"; minimum = 100; maximum = 10000; default = 1500 }
    }
    $spreadProfitabilityProperties = [pscustomobject]@{
        universe = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 1; maxItems = 500 }
        venues = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 2 }
        quantity = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 100 }
    }
    $spreadLivePlanProperties = [pscustomobject]@{
        universe = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 1; maxItems = 500 }
        venues = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 2 }
        quantity = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 100 }
        max_loss_usd = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 15 }
        max_notional_usd = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 1500 }
    }
    $spreadBriefProperties = [pscustomobject]@{
        universe = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 1; maxItems = 500 }
        venues = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; minItems = 2 }
        quantity = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 100 }
        max_loss_usd = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 15 }
        max_notional_usd = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 1500 }
    }
    $liveSteeringStateProperties = [pscustomobject]@{
        universe = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" } }
        venues = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" } }
        quantity = [pscustomobject]@{ type = "number"; exclusiveMinimum = 0; default = 100 }
    }
    $liveSteeringProperties = [pscustomobject]@{
        symbol = [pscustomobject]@{ type = "string" }
        buy_venue = [pscustomobject]@{ type = "string" }
        sell_venue = [pscustomobject]@{ type = "string" }
        realized_pnl_usd = [pscustomobject]@{ type = "number"; default = 0 }
        slippage_overshoot_bps = [pscustomobject]@{ type = "number"; default = 0 }
        fill_latency_ms = [pscustomobject]@{ type = "integer"; minimum = 0; default = 0 }
        loss_floor_usd = [pscustomobject]@{ type = "number"; default = 0 }
        exit_edge_floor_bps = [pscustomobject]@{ type = "number"; default = 0.2 }
        max_slippage_overshoot_bps = [pscustomobject]@{ type = "number"; default = 2.0 }
    }
    $operatorPacketProperties = [pscustomobject]@{
        symbol = [pscustomobject]@{ type = "string" }
        buy_venue = [pscustomobject]@{ type = "string" }
        sell_venue = [pscustomobject]@{ type = "string" }
        realized_pnl_usd = [pscustomobject]@{ type = "number"; default = 0 }
        slippage_overshoot_bps = [pscustomobject]@{ type = "number"; default = 0 }
        fill_latency_ms = [pscustomobject]@{ type = "integer"; minimum = 0; default = 0 }
        loss_floor_usd = [pscustomobject]@{ type = "number"; default = 0 }
    }
    return [pscustomobject]@{
        tools = @(
            [pscustomobject]@{ name = "get_agent_status"; description = "Read current agent availability, wake timing, and next action."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_queue_summary"; description = "Read queue, active, failed, and recent done task summaries."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_recent_failures"; description = "Read recent failed tasks and blocked slots."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ limit = [pscustomobject]@{ type = "integer"; minimum = 1; maximum = 50; default = 10 } }) },
            [pscustomobject]@{ name = "get_latest_agent_logs"; description = "Read latest observed log tails for each agent slot."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_mcp_capability_status"; description = "Read MCP connector online/read-only/write capability status."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_mcp_feature_overview"; description = "Read grouped MCP feature availability and known missing ops gaps."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_tunnel_canary_status"; description = "Send a read-only tools/list canary through local MCP and the configured tunnel."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_active_fleet_plan"; description = "Read the autonomous fleet dispatch plan without starting agents or moving tasks."; inputSchema = $empty },
            [pscustomobject]@{ name = "sync_repository"; description = "Safely fast-forward sync the local orchestrator repository. Defaults to dry_run=false and ff-only helper behavior."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ remote = [pscustomobject]@{ type = "string"; default = "origin" }; branch = [pscustomobject]@{ type = "string"; default = "master" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; plan_only = [pscustomobject]@{ type = "boolean"; default = $false }; allow_dirty = [pscustomobject]@{ type = "boolean"; default = $false } }) },
            [pscustomobject]@{ name = "requeue_task"; description = "Move a task markdown file back to tasks/queue through the audited helper."; inputSchema = New-ObjectSchema -Properties $taskProperties -Required @("task_path") },
            [pscustomobject]@{ name = "fail_task"; description = "Move a task markdown file to tasks/failed through the audited helper."; inputSchema = New-ObjectSchema -Properties $taskProperties -Required @("task_path") },
            [pscustomobject]@{ name = "complete_task"; description = "Move a task markdown file to tasks/done through the audited helper."; inputSchema = New-ObjectSchema -Properties $taskProperties -Required @("task_path") },
            [pscustomobject]@{ name = "start_agent"; description = "Start a selected agent slot once through the audited helper."; inputSchema = New-ObjectSchema -Properties $agentProperties -Required @("slot") },
            [pscustomobject]@{ name = "rerun_agent"; description = "Rerun a selected agent slot once through the audited helper."; inputSchema = New-ObjectSchema -Properties $agentProperties -Required @("slot") },
            [pscustomobject]@{ name = "get_github_issues_cached"; description = "Read cached GitHub issues from alex-place/gm-agent-orchestrator. Data is cached for 30 seconds."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_github_pr_status_cached"; description = "Read cached GitHub PR metadata from alex-place/gm-agent-orchestrator. Data is cached for 30 seconds."; inputSchema = $empty },
            [pscustomobject]@{ name = "get_github_pr_detail"; description = "Read full detail for a specific PR: body, head SHA, branch names, mergeable state, file counts. Required for PR review."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ pr_number = [pscustomobject]@{ type = "integer"; minimum = 1; description = "GitHub PR number" } }) -Required @("pr_number") },
            [pscustomobject]@{ name = "get_github_pr_files"; description = "Read changed files list for a specific PR: filename, status, additions, deletions, and patch diff per file."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ pr_number = [pscustomobject]@{ type = "integer"; minimum = 1; description = "GitHub PR number" } }) -Required @("pr_number") },
            [pscustomobject]@{ name = "get_github_pr_checks"; description = "Read CI check run statuses for a specific PR's head commit: check name, status, and conclusion."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ pr_number = [pscustomobject]@{ type = "integer"; minimum = 1; description = "GitHub PR number" } }) -Required @("pr_number") },
            [pscustomobject]@{ name = "get_github_pr_comments"; description = "Read review and issue comments on a specific PR: author, body, file path and line for inline review comments."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ pr_number = [pscustomobject]@{ type = "integer"; minimum = 1; description = "GitHub PR number" } }) -Required @("pr_number") },
            [pscustomobject]@{ name = "update_github_issue_comment"; description = "Update an existing GitHub issue comment in alex-place/gm-agent-orchestrator through the guarded helper. Use dry_run=true before mutation."; inputSchema = New-ObjectSchema -Properties $commentProperties -Required @("comment_id") },
            [pscustomobject]@{ name = "propose_powershell_patch"; description = "Stage a PowerShell patch payload for later validation or promotion. Does not modify live files."; inputSchema = New-ObjectSchema -Properties $patchProperties },
            [pscustomobject]@{ name = "validate_powershell_patch"; description = "Validate a staged PowerShell patch with parser checks."; inputSchema = New-ObjectSchema -Properties $patchProperties -Required @("patch_id") },
            [pscustomobject]@{ name = "promote_powershell_patch"; description = "Promote a staged PowerShell patch with backup support. Defaults to dry_run=true."; inputSchema = New-ObjectSchema -Properties $patchProperties -Required @("patch_id") },
            [pscustomobject]@{ name = "run_safe_powershell"; description = "Run a PowerShell script safely through the orchestrator. For security, only pre-approved scripts can be executed by name."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ script_name = [pscustomobject]@{ type = "string" }; argument_json = [pscustomobject]@{ type = "string" }; argument_json_base64 = [pscustomobject]@{ type = "string" }; arguments = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" } }; dry_run = [pscustomobject]@{ type = "boolean"; default = $false }; plan_only = [pscustomobject]@{ type = "boolean"; default = $false }; timeout_seconds = [pscustomobject]@{ type = "integer"; minimum = 1; maximum = 600; default = 30 } }) -Required @("script_name") },
            [pscustomobject]@{ name = "restart_mcp_server"; description = "Schedule a guarded restart of this orchestrator MCP server. Defaults to dry_run=true and returns before any live restart."; inputSchema = New-ObjectSchema -Properties $restartProperties -Required @("reason") },
            [pscustomobject]@{ name = "run_service_supervisor"; description = "Run the local service supervisor once to check or start offline services. Defaults to dry_run=true."; inputSchema = New-ObjectSchema -Properties $supervisorProperties },
            [pscustomobject]@{ name = "get_ibkr_quotes"; description = "Read-only IBKR top-of-book quote snapshot for one or more symbols."; inputSchema = New-ObjectSchema -Properties $ibkrQuotesProperties -Required @("symbols") },
            [pscustomobject]@{ name = "get_ibkr_orderbook"; description = "Read-only IBKR depth snapshot for one symbol."; inputSchema = New-ObjectSchema -Properties $ibkrOrderbookProperties -Required @("symbol") },
            [pscustomobject]@{ name = "get_ibkr_positions"; description = "Read-only IBKR account positions and exposure summary."; inputSchema = New-ObjectSchema -Properties $ibkrPositionsProperties },
            [pscustomobject]@{ name = "get_ibkr_account_risk"; description = "Read-only IBKR account-level risk and margin telemetry."; inputSchema = New-ObjectSchema -Properties $ibkrRiskProperties },
            [pscustomobject]@{ name = "rank_spread_opportunities"; description = "Paper-only spread ranking across venues using read-only quote snapshots."; inputSchema = New-ObjectSchema -Properties $spreadRankProperties -Required @("universe", "venues") },
            [pscustomobject]@{ name = "simulate_spread_trade"; description = "Paper-only spread trade simulation with fee/slippage modeling and no execution side effects."; inputSchema = New-ObjectSchema -Properties $spreadSimProperties -Required @("symbol", "buy_venue", "sell_venue", "quantity") },
            [pscustomobject]@{ name = "get_spread_execution_readiness"; description = "Truth-bounded go/no-go gate for promoting spread flow from paper simulation to live connector execution checks."; inputSchema = New-ObjectSchema -Properties $spreadReadinessProperties },
            [pscustomobject]@{ name = "get_spread_profitability_snapshot"; description = "Truth-bounded paper profitability snapshot combining spread ranking, simulation, and readiness gate evidence."; inputSchema = New-ObjectSchema -Properties $spreadProfitabilityProperties },
            [pscustomobject]@{ name = "plan_spread_live_micro_experiment"; description = "Create a guarded, truth-bounded live micro-experiment plan from current spread readiness and profitability evidence."; inputSchema = New-ObjectSchema -Properties $spreadLivePlanProperties },
            [pscustomobject]@{ name = "create_spread_experiment_brief"; description = "Create a GitHub-ready markdown brief for a guarded spread live micro-experiment based on current truth-bounded evidence."; inputSchema = New-ObjectSchema -Properties $spreadBriefProperties },
            [pscustomobject]@{ name = "get_live_steering_state"; description = "Read current spread steering state from readiness and profitability evidence."; inputSchema = New-ObjectSchema -Properties $liveSteeringStateProperties },
            [pscustomobject]@{ name = "steer_live_spread_trade"; description = "Emit a real-time spread execution action: enter, hold, reduce, exit_now, or kill_switch."; inputSchema = New-ObjectSchema -Properties $liveSteeringProperties },
            [pscustomobject]@{ name = "get_spread_operator_packet"; description = "Generate a GitHub-ready markdown steering update packet with action, risk thresholds, and evidence."; inputSchema = New-ObjectSchema -Properties $operatorPacketProperties },
            [pscustomobject]@{ name = "create_queue_task"; description = "Create an orchestrator queue task through the audited queue helper. Use dry_run=true to preview."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ title = [pscustomobject]@{ type = "string" }; body = [pscustomobject]@{ type = "string" }; reason = [pscustomobject]@{ type = "string" }; priority = [pscustomobject]@{ type = "string"; enum = @("P0", "P1", "P2"); default = "P1" }; owner = [pscustomobject]@{ type = "string"; enum = @("claude", "codex", "gemini", "gpt", "human", "operator-intake"); default = "claude" }; blocked_by = [pscustomobject]@{ type = "string" }; dry_run = [pscustomobject]@{ type = "boolean"; default = $true } }) -Required @("title") },
            [pscustomobject]@{ name = "get_gamemaker_project_info"; description = "Read GameMaker project metadata (name, version, resource count)."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_gamemaker_compiler_errors"; description = "Parse GameMaker compiler output and return structured error list with line numbers."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_sprite_asset_status"; description = "Validate sprite imports, frame counts, and dimensions in the GameMaker project."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_room_editor_status"; description = "Validate room layouts, object placements, and room structure integrity."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) },
            [pscustomobject]@{ name = "get_game_build_status"; description = "Aggregate build status: compiler errors, asset validation, room structure (all Phase 1 checks)."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ project = [pscustomobject]@{ type = "string"; default = "child-of-levistus" } }) }
        )
    }
}

function Invoke-PowerShellPatchTool {
    param(
        [string]$Action,
        [object]$Arguments
    )

    if ($null -eq $Arguments) { $Arguments = [pscustomobject]@{} }

    $patchId = ""
    $targetPath = ""
    $contentPath = ""
    $reason = ""
    $dryRun = $false

    $v = Get-JsonRpcProperty -Object $Arguments -Name "patch_id"; if ($null -ne $v) { $patchId = [string]$v }
    $v = Get-JsonRpcProperty -Object $Arguments -Name "target_path"; if ($null -ne $v) { $targetPath = [string]$v }
    $v = Get-JsonRpcProperty -Object $Arguments -Name "content_path"; if ($null -ne $v) { $contentPath = [string]$v }
    $v = Get-JsonRpcProperty -Object $Arguments -Name "reason"; if ($null -ne $v) { $reason = [string]$v }
    $v = Get-JsonRpcProperty -Object $Arguments -Name "dry_run"; if ($null -ne $v) { $dryRun = [bool]$v }

    if ($Action -eq "promote" -and $null -eq (Get-JsonRpcProperty -Object $Arguments -Name "dry_run")) {
        $dryRun = $true
    }

    $cmd = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$PowerShellPatchScript,"-Root",$Root,"-Action",$Action)

    if (-not [string]::IsNullOrWhiteSpace($patchId)) { $cmd += @("-PatchId",$patchId) }
    if (-not [string]::IsNullOrWhiteSpace($targetPath)) { $cmd += @("-TargetPath",$targetPath) }
    if (-not [string]::IsNullOrWhiteSpace($contentPath)) { $cmd += @("-ContentPath",$contentPath) }
    if (-not [string]::IsNullOrWhiteSpace($reason)) { $cmd += @("-Reason",$reason) }
    if ($dryRun) { $cmd += "-DryRun" }

    $output = @(& powershell @cmd 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { throw "PowerShell patch helper emitted no output: $PowerShellPatchScript" }

    try { $null = $text | ConvertFrom-Json -ErrorAction Stop }
    catch { throw "PowerShell patch helper emitted invalid JSON: $($_.Exception.Message). Output: $text" }

    if ($exitCode -ne 0) { throw "PowerShell patch helper failed with exit code $($exitCode): $text" }

    return $text
}

function Invoke-ToolCall {
    param([string]$Name, [object]$Arguments)
    switch ($Name) {
        "get_agent_status" { return New-ToolTextResult -Value (Get-AgentStatusTool) }
        "get_queue_summary" { return New-ToolTextResult -Value (Get-QueueSummaryTool) }
        "get_recent_failures" {
            $limit = 10
            $requestedLimit = Get-OptionalJsonProperty -Object $Arguments -Name "limit"
            if ($null -ne $requestedLimit) {
                $limit = [Math]::Max(1, [Math]::Min(50, [int]$requestedLimit))
            }
            return New-ToolTextResult -Value (Get-RecentFailuresTool -Limit $limit)
        }
        "get_latest_agent_logs" { return New-ToolTextResult -Value (Get-LatestAgentLogsTool) }
        "get_mcp_capability_status" { return New-ToolTextResult -Value (Get-McpCapabilityStatusTool) }
        "get_mcp_feature_overview" { return New-ToolTextResult -Value (Get-McpFeatureOverviewTool) }
        "get_tunnel_canary_status" { return New-ToolTextResult -Value (Get-TunnelCanaryStatusTool) }
        "get_active_fleet_plan" { return New-ToolTextResult -Value (Get-ActiveFleetPlanTool) }
        "sync_repository" { return New-ToolTextResult -Value (Invoke-SyncRepositoryTool -Arguments $Arguments) }
        "requeue_task" { return New-ToolTextResult -Value (Invoke-TaskActionTool -Action "requeue_task" -Arguments $Arguments) }
        "fail_task" { return New-ToolTextResult -Value (Invoke-TaskActionTool -Action "fail_task" -Arguments $Arguments) }
        "complete_task" { return New-ToolTextResult -Value (Invoke-TaskActionTool -Action "complete_task" -Arguments $Arguments) }
        "start_agent" { return New-ToolTextResult -Value (Invoke-AgentActionTool -Action "start_agent" -Arguments $Arguments) }
        "rerun_agent" { return New-ToolTextResult -Value (Invoke-AgentActionTool -Action "rerun_agent" -Arguments $Arguments) }
        "get_github_issues_cached" { return New-ToolTextResult -Value (Get-GitHubIssuesCachedTool) }
        "get_github_pr_status_cached" { return New-ToolTextResult -Value (Get-GitHubPrStatusCachedTool) }
        "get_github_pr_detail" { $prNum = 0; $v = Get-JsonRpcProperty -Object $Arguments -Name "pr_number"; if ($null -ne $v) { $prNum = [int]$v }; return New-ToolTextResult -Value (Get-GitHubPrDetailTool -PrNumber $prNum) }
        "get_github_pr_files" { $prNum = 0; $v = Get-JsonRpcProperty -Object $Arguments -Name "pr_number"; if ($null -ne $v) { $prNum = [int]$v }; return New-ToolTextResult -Value (Get-GitHubPrFilesTool -PrNumber $prNum) }
        "get_github_pr_checks" { $prNum = 0; $v = Get-JsonRpcProperty -Object $Arguments -Name "pr_number"; if ($null -ne $v) { $prNum = [int]$v }; return New-ToolTextResult -Value (Get-GitHubPrChecksTool -PrNumber $prNum) }
        "get_github_pr_comments" { $prNum = 0; $v = Get-JsonRpcProperty -Object $Arguments -Name "pr_number"; if ($null -ne $v) { $prNum = [int]$v }; return New-ToolTextResult -Value (Get-GitHubPrCommentsTool -PrNumber $prNum) }
        "update_github_issue_comment" { return New-ToolTextResult -Value (Update-GitHubIssueCommentTool -Arguments $Arguments) }
        "propose_powershell_patch" { return New-ToolTextResult -Value (Invoke-PowerShellPatchTool -Action "propose" -Arguments $Arguments) }
        "validate_powershell_patch" { return New-ToolTextResult -Value (Invoke-PowerShellPatchTool -Action "validate" -Arguments $Arguments) }
        "promote_powershell_patch" { return New-ToolTextResult -Value (Invoke-PowerShellPatchTool -Action "promote" -Arguments $Arguments) }
        "run_safe_powershell" { return New-ToolTextResult -Value (Invoke-SafePowerShellRunnerTool -Arguments $Arguments) }
        "restart_mcp_server" { return New-ToolTextResult -Value (Restart-McpServerTool -Arguments $Arguments) }
        "run_service_supervisor" { return New-ToolTextResult -Value (Run-ServiceSupervisorTool -Arguments $Arguments) }
        "get_ibkr_quotes" { return New-ToolTextResult -Value (Get-IbkrQuotesTool -Arguments $Arguments) }
        "get_ibkr_orderbook" { return New-ToolTextResult -Value (Get-IbkrOrderbookTool -Arguments $Arguments) }
        "get_ibkr_positions" { return New-ToolTextResult -Value (Get-IbkrPositionsTool -Arguments $Arguments) }
        "get_ibkr_account_risk" { return New-ToolTextResult -Value (Get-IbkrAccountRiskTool -Arguments $Arguments) }
        "rank_spread_opportunities" { return New-ToolTextResult -Value (Rank-SpreadOpportunitiesTool -Arguments $Arguments) }
        "simulate_spread_trade" { return New-ToolTextResult -Value (Simulate-SpreadTradeTool -Arguments $Arguments) }
        "get_spread_execution_readiness" { return New-ToolTextResult -Value (Get-SpreadExecutionReadinessTool -Arguments $Arguments) }
        "get_spread_profitability_snapshot" { return New-ToolTextResult -Value (Get-SpreadProfitabilitySnapshotTool -Arguments $Arguments) }
        "plan_spread_live_micro_experiment" { return New-ToolTextResult -Value (Plan-SpreadLiveMicroExperimentTool -Arguments $Arguments) }
        "create_spread_experiment_brief" { return New-ToolTextResult -Value (Create-SpreadExperimentBriefTool -Arguments $Arguments) }
        "get_live_steering_state" { return New-ToolTextResult -Value (Get-LiveSteeringStateTool -Arguments $Arguments) }
        "steer_live_spread_trade" { return New-ToolTextResult -Value (Steer-LiveSpreadTradeTool -Arguments $Arguments) }
        "get_spread_operator_packet" { return New-ToolTextResult -Value (Get-SpreadOperatorPacketTool -Arguments $Arguments) }
        "create_queue_task" { return New-ToolTextResult -Value (Invoke-CreateQueueTaskTool -Arguments $Arguments) }
        "get_gamemaker_project_info" { return New-ToolTextResult -Value (Get-GameMakerProjectInfoTool -Arguments $Arguments) }
        "get_gamemaker_compiler_errors" { return New-ToolTextResult -Value (Get-GameMakerCompilerErrorsTool -Arguments $Arguments) }
        "get_sprite_asset_status" { return New-ToolTextResult -Value (Get-GameMakerSpriteAssetStatusTool -Arguments $Arguments) }
        "get_room_editor_status" { return New-ToolTextResult -Value (Get-GameMakerRoomEditorStatusTool -Arguments $Arguments) }
        "get_game_build_status" { return New-ToolTextResult -Value (Get-GameMakerBuildStatusTool -Arguments $Arguments) }
        default { throw "Unknown tool: $Name" }
    }
}

function Get-JsonRpcProperty {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    if ($null -eq $Object.PSObject.Properties[$Name]) { return $null }
    return $Object.PSObject.Properties[$Name].Value
}
