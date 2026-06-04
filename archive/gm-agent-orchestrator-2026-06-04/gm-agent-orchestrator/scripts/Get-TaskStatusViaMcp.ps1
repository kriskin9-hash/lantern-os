<#
.SYNOPSIS
Query task status via the orchestrator MCP interface.

.DESCRIPTION
This script replaces PowerShell-based status queries with HTTP calls to the
orchestrator MCP endpoint, eliminating the need for elevation prompts.

.PARAMETER TaskId
The task ID or title to query (optional - returns all if not specified).

.PARAMETER McpUri
The MCP server URI. Default: http://127.0.0.1:8787

.PARAMETER Format
Output format: json, table, or detailed
Default: table

.EXAMPLE
.\Get-TaskStatusViaMcp.ps1

.EXAMPLE
.\Get-TaskStatusViaMcp.ps1 -TaskId "task-001" -Format detailed

.EXAMPLE
.\Get-TaskStatusViaMcp.ps1 -Format json | ConvertFrom-Json | Select-Object -ExpandProperty tasks

.NOTES
Requires: MCP server running on localhost:8787
Cost: Zero elevation prompts, HTTP-based queries
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$TaskId = "",

    [Parameter()]
    [string]$McpUri = "http://127.0.0.1:8787",

    [Parameter()]
    [ValidateSet("json", "table", "detailed")]
    [string]$Format = "table"
)

$ErrorActionPreference = "Stop"

# Health check
Write-Verbose "Checking MCP server health at $McpUri/health..."
try {
    $health = Invoke-RestMethod -Uri "$McpUri/health" -TimeoutSec 5 -ErrorAction Stop
    if (-not ($health.ok -and $health.service -eq "gm-agent-orchestrator-mcp")) {
        throw "MCP server not responding with expected health status"
    }
} catch {
    Write-Error "MCP server is not available at $McpUri"
    Write-Error "Start it with: .\scripts\Start-OrchMcpServer.ps1"
    throw
}

# Query current task state
Write-Verbose "Querying task state from MCP..."
try {
    # Build query payload
    $query = @{
        jsonrpc = "2.0"
        id = 1
        method = "get_tasks"
        params = if ($TaskId) {
            @{ filter = $TaskId }
        } else {
            @{}
        }
    } | ConvertTo-Json

    $response = Invoke-RestMethod `
        -Uri "$McpUri/mcp" `
        -Method POST `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body $query `
        -TimeoutSec 10

    if (-not $response.result) {
        Write-Warning "No tasks found"
        return
    }

    $tasks = $response.result.tasks

    # Format output
    switch ($Format) {
        "json" {
            $tasks | ConvertTo-Json -Depth 10
        }

        "table" {
            $displayTasks = $tasks | Select-Object `
                @{ Name = "ID"; Expression = { $_.id } },
                @{ Name = "Title"; Expression = { $_.title } },
                @{ Name = "State"; Expression = { $_.state } },
                @{ Name = "Agent"; Expression = { $_.owner } },
                @{ Name = "Age"; Expression = {
                    $age = [datetime]::UtcNow - [datetime]::Parse($_.createdAt)
                    if ($age.TotalSeconds -lt 60) {
                        "$([int]$age.TotalSeconds)s"
                    } elseif ($age.TotalMinutes -lt 60) {
                        "$([int]$age.TotalMinutes)m"
                    } else {
                        "$([int]$age.TotalHours)h"
                    }
                } }

            if ($displayTasks) {
                $displayTasks | Format-Table -AutoSize
            }
        }

        "detailed" {
            foreach ($task in $tasks) {
                Write-Host ""
                Write-Host "Task: $($task.id)" -ForegroundColor Cyan
                Write-Host "Title: $($task.title)" -ForegroundColor White
                $stateDisplay = switch ($task.state) {
                    'queue' { "$($task.state) [waiting]" }
                    'active' { "$($task.state) [in progress]" }
                    'done' { "$($task.state) [complete]" }
                    'failed' { "$($task.state) [error]" }
                    'blocked' { "$($task.state) [blocked]" }
                    default { $task.state }
                }
                $stateColor = @{
                    'queue' = 'Yellow'
                    'active' = 'Cyan'
                    'done' = 'Green'
                    'failed' = 'Red'
                    'blocked' = 'Magenta'
                }[$task.state]
                Write-Host "State: $stateDisplay" -ForegroundColor $stateColor
                Write-Host "Owner: $($task.owner)"
                Write-Host "Created: $($task.createdAt)"
                Write-Host "Priority: $($task.priority)"

                if ($task.agent) {
                    Write-Host "Current Agent: $($task.agent)"
                }
                if ($task.error) {
                    Write-Host "Error: $($task.error)" -ForegroundColor Red
                }
                if ($task.notes) {
                    Write-Host "Notes: $($task.notes)"
                }
            }
        }
    }

    return $tasks

} catch {
    Write-Error "Failed to query task status: $($_.Exception.Message)"
    throw
}
