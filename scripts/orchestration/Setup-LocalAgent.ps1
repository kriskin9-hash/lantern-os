[CmdletBinding()]
param(
    [ValidateSet('lmstudio', 'llmster', 'ollama')]
    [string]$Provider = 'lmstudio',

    [string]$BaseUrl = '',
    [string]$Model = 'lfm2-24b-a2b',
    [switch]$SkipSmokeTest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path "$PSScriptRoot\..").Path

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    switch ($Provider) {
        'lmstudio' { $BaseUrl = 'http://localhost:1234/v1' }
        'llmster' { $BaseUrl = 'http://localhost:1234/v1' }
        'ollama' { $BaseUrl = 'http://localhost:11434/v1' }
    }
}

$envPath = Join-Path $root '.env.local'
$envContent = @"
LOCAL_LLM_ENABLED=true
LOCAL_LLM_PROVIDER=$Provider
LOCAL_LLM_BASE_URL=$BaseUrl
LOCAL_LLM_MODEL=$Model
LOCAL_LLM_MAX_INPUT_TOKENS=8192
LOCAL_LLM_MAX_OUTPUT_TOKENS=1024
LOCAL_LLM_TIMEOUT_MS=60000
LOCAL_LLM_TEMPERATURE=0.1
LOCAL_LLM_MODE=read_only
"@

Set-Content -Path $envPath -Value $envContent -Encoding UTF8

$env:LOCAL_LLM_ENABLED = 'true'
$env:LOCAL_LLM_PROVIDER = $Provider
$env:LOCAL_LLM_BASE_URL = $BaseUrl
$env:LOCAL_LLM_MODEL = $Model
$env:LOCAL_LLM_MAX_INPUT_TOKENS = '8192'
$env:LOCAL_LLM_MAX_OUTPUT_TOKENS = '1024'
$env:LOCAL_LLM_TIMEOUT_MS = '60000'
$env:LOCAL_LLM_TEMPERATURE = '0.1'
$env:LOCAL_LLM_MODE = 'read_only'

Write-Host "Local agent configuration written to $envPath"
Write-Host "Provider: $Provider"
Write-Host "Base URL: $BaseUrl"
Write-Host "Model: $Model"

if ($SkipSmokeTest) {
    Write-Host 'Skipping smoke test by request.'
    exit 0
}

$testScript = Join-Path $root 'scripts\Test-LocalModel.ps1'
$routerScript = Join-Path $root 'scripts\Invoke-LocalRouter.ps1'

if (!(Test-Path $testScript)) {
    throw "Missing smoke test script: $testScript"
}

if (!(Test-Path $routerScript)) {
    throw "Missing local router script: $routerScript"
}

Write-Host 'Running local model smoke test...'
& powershell -NoProfile -ExecutionPolicy Bypass -File $testScript -BaseUrl $BaseUrl -Model $Model
if ($LASTEXITCODE -ne 0) {
    throw "Local model smoke test failed with exit code $LASTEXITCODE. Start the $Provider OpenAI-compatible server and retry."
}

Write-Host 'Running local router classification test...'
& powershell -NoProfile -ExecutionPolicy Bypass -File $routerScript -BaseUrl $BaseUrl -Model $Model -Task 'Classify this task: summarize logs from a failed unit test.'
if ($LASTEXITCODE -ne 0) {
    throw "Local router test failed with exit code $LASTEXITCODE."
}

Write-Host 'Local agent setup verified.'
