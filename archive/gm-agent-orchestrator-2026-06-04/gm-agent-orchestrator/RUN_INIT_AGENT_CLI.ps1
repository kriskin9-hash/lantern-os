param(
    [ValidateSet("all", "claude", "codex")]
    [string]$Agent = "all",
    [switch]$LaunchClaudeInteractive,
    [switch]$LaunchCodexInteractive
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $root "scripts\Initialize-AgentCli.ps1"

if (!(Test-Path -LiteralPath $script)) {
    throw "Missing init script: $script. Run git pull, then try again."
}

$argsList = @("-OrchestratorRoot", $root, "-Agent", $Agent)
if ($LaunchClaudeInteractive) { $argsList += "-LaunchClaudeInteractive" }
if ($LaunchCodexInteractive) { $argsList += "-LaunchCodexInteractive" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $script @argsList
