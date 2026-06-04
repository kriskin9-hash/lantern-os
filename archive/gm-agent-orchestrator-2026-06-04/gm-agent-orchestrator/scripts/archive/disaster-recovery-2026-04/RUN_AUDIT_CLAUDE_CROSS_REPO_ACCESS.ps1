$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $root "scripts\Test-ClaudeCrossRepoAccess.ps1"

if (!(Test-Path -LiteralPath $script)) {
    throw "Missing audit script: $script. Run git pull, then try again."
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $script -OrchestratorRoot $root
