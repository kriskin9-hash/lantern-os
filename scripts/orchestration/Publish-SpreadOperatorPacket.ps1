[CmdletBinding()]
param(
    [string]$McpUrl = "http://127.0.0.1:8787/mcp",
    [string]$PacketPath = "C:\tmp\spread-ops\spread-operator-packet-latest.md",
    [int]$CommentId = 0,
    [switch]$WriteComment
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PacketPath -PathType Leaf)) {
    throw "Packet file not found: $PacketPath"
}

$packet = Get-Content -LiteralPath $PacketPath -Raw
if ([string]::IsNullOrWhiteSpace($packet)) {
    throw "Packet file is empty: $PacketPath"
}

$result = [ordered]@{
    ok = $true
    generatedAt = (Get-Date).ToString("o")
    packetPath = $PacketPath
    packetLength = $packet.Length
    writeComment = [bool]$WriteComment
    dryRun = $true
}

if ($WriteComment) {
    if ($CommentId -le 0) { throw "When -WriteComment is set, -CommentId must be > 0." }
    $body = @{
        jsonrpc = "2.0"
        id = "update-comment"
        method = "tools/call"
        params = @{
            name = "update_github_issue_comment"
            arguments = @{
                comment_id = $CommentId
                body = $packet
                dry_run = $false
            }
        }
    } | ConvertTo-Json -Depth 20
    $resp = Invoke-RestMethod -Uri $McpUrl -Method Post -ContentType "application/json" -Body $body
    $result.dryRun = $false
    $result.response = $resp
}
else {
    $result.preview = $packet
}

$result | ConvertTo-Json -Depth 20
