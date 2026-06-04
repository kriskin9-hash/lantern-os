if ((Get-Variable -Name GitWorkflowToolsLoaded -Scope Script -ErrorAction SilentlyContinue) -and $script:GitWorkflowToolsLoaded) { return }
$script:GitWorkflowToolsLoaded = $true
$script:BaseGetToolsListForGitWorkflow = (Get-Command Get-ToolsList -CommandType Function).ScriptBlock
$script:BaseInvokeToolCallForGitWorkflow = (Get-Command Invoke-ToolCall -CommandType Function).ScriptBlock

function Invoke-GitWorkflowTool {
    param(
        [string]$Action,
        [object]$Arguments,
        [bool]$Mutation = $false
    )

    if ($null -eq $Arguments) { $Arguments = [pscustomobject]@{} }

    $args = @("-Root", $Root, "-Action", $Action)

    $branchName = Get-OptionalJsonProperty -Object $Arguments -Name "branch_name"
    if (-not [string]::IsNullOrWhiteSpace([string]$branchName)) { $args += @("-BranchName", [string]$branchName) }

    $paths = Get-OptionalJsonProperty -Object $Arguments -Name "paths"
    if ($null -ne $paths) { $args += @("-PathsJson", (ConvertTo-Json -InputObject @($paths) -Depth 20 -Compress)) }

    $message = Get-OptionalJsonProperty -Object $Arguments -Name "message"
    if (-not [string]::IsNullOrWhiteSpace([string]$message)) { $args += @("-Message", [string]$message) }

    $remote = Get-OptionalJsonProperty -Object $Arguments -Name "remote"
    if (-not [string]::IsNullOrWhiteSpace([string]$remote)) { $args += @("-Remote", [string]$remote) }

    $baseBranch = Get-OptionalJsonProperty -Object $Arguments -Name "base_branch"
    if (-not [string]::IsNullOrWhiteSpace([string]$baseBranch)) { $args += @("-BaseBranch", [string]$baseBranch) }

    $title = Get-OptionalJsonProperty -Object $Arguments -Name "title"
    if (-not [string]::IsNullOrWhiteSpace([string]$title)) { $args += @("-Title", [string]$title) }

    $body = Get-OptionalJsonProperty -Object $Arguments -Name "body"
    if (-not [string]::IsNullOrWhiteSpace([string]$body)) { $args += @("-Body", [string]$body) }

    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"
    if ($Mutation) {
        if ($null -eq $dryRun -or $true -eq [bool]$dryRun) { $args += "-DryRun" }
    }
    elseif ($true -eq [bool]$dryRun) {
        $args += "-DryRun"
    }

    return Invoke-JsonScript -ScriptPath $GitWorkflowScript -Arguments $args
}

function Get-GitWorkflowToolSchemas {
    $empty = New-ObjectSchema -Properties ([pscustomobject]@{})
    $dryRunProperty = [pscustomobject]@{ type = "boolean"; default = $true; description = "Preview the operation without changing git/GitHub state. Defaults to true for mutations." }
    return @(
        [pscustomobject]@{ name = "get_git_status_summary"; description = "Read current branch, changed files, staged files, and protected-branch status for the orchestrator repo."; inputSchema = $empty },
        [pscustomobject]@{ name = "get_worktree_risk_summary"; description = "Read git status plus a low/medium/high worktree risk assessment before mutations."; inputSchema = $empty },
        [pscustomobject]@{ name = "create_branch"; description = "Create and checkout a feature branch in the orchestrator repo. Refuses master/main. Defaults to dry-run."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ branch_name = [pscustomobject]@{ type = "string"; description = "Feature branch name to create." }; dry_run = $dryRunProperty }) -Required @("branch_name") },
        [pscustomobject]@{ name = "stage_files"; description = "Stage explicit repo-relative file paths only. Refuses absolute paths, traversal, wildcards, and protected branches. Defaults to dry-run."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ paths = [pscustomobject]@{ type = "array"; items = [pscustomobject]@{ type = "string" }; description = "Repo-relative paths to stage." }; dry_run = $dryRunProperty }) -Required @("paths") },
        [pscustomobject]@{ name = "commit_staged_changes"; description = "Commit currently staged changes on a feature branch. Refuses master/main and defaults to dry-run."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ message = [pscustomobject]@{ type = "string"; description = "Commit message." }; dry_run = $dryRunProperty }) -Required @("message") },
        [pscustomobject]@{ name = "push_current_branch"; description = "Push the current feature branch with upstream tracking. Refuses master/main and defaults to dry-run."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ remote = [pscustomobject]@{ type = "string"; default = "origin" }; dry_run = $dryRunProperty }) },
        [pscustomobject]@{ name = "open_pr"; description = "Open a GitHub PR for the current feature branch using gh. Refuses master/main and defaults to dry-run."; inputSchema = New-ObjectSchema -Properties ([pscustomobject]@{ title = [pscustomobject]@{ type = "string" }; body = [pscustomobject]@{ type = "string" }; base_branch = [pscustomobject]@{ type = "string"; default = "master" }; dry_run = $dryRunProperty }) -Required @("title") }
    )
}

function Get-ToolsList {
    $result = & $script:BaseGetToolsListForGitWorkflow
    $existing = @($result.tools)
    $result.tools = @($existing + (Get-GitWorkflowToolSchemas))
    return $result
}

function Invoke-ToolCall {
    param([string]$Name, [object]$Arguments)

    switch ($Name) {
        "get_git_status_summary" { return New-ToolTextResult -Value (Invoke-GitWorkflowTool -Action "git_status" -Arguments $Arguments) }
        "get_worktree_risk_summary" { return New-ToolTextResult -Value (Invoke-GitWorkflowTool -Action "worktree_risk" -Arguments $Arguments) }
        "create_branch" { return New-ToolTextResult -Value (Invoke-GitWorkflowTool -Action "create_branch" -Arguments $Arguments -Mutation $true) }
        "stage_files" { return New-ToolTextResult -Value (Invoke-GitWorkflowTool -Action "stage_files" -Arguments $Arguments -Mutation $true) }
        "commit_staged_changes" { return New-ToolTextResult -Value (Invoke-GitWorkflowTool -Action "commit_staged_changes" -Arguments $Arguments -Mutation $true) }
        "push_current_branch" { return New-ToolTextResult -Value (Invoke-GitWorkflowTool -Action "push_current_branch" -Arguments $Arguments -Mutation $true) }
        "open_pr" { return New-ToolTextResult -Value (Invoke-GitWorkflowTool -Action "open_pr" -Arguments $Arguments -Mutation $true) }
        default { return & $script:BaseInvokeToolCallForGitWorkflow -Name $Name -Arguments $Arguments }
    }
}


