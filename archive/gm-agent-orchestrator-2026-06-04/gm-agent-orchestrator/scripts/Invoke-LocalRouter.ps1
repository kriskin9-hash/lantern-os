[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Task,

  [string]$BaseUrl = $(if ($env:LOCAL_LLM_BASE_URL) { $env:LOCAL_LLM_BASE_URL } else { 'http://localhost:1234/v1' }),
  [string]$Model = $(if ($env:LOCAL_LLM_MODEL) { $env:LOCAL_LLM_MODEL } else { 'lfm2-24b-a2b' }),
  [string]$RouterJson = '',
  [switch]$PolicyOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-JsonPropertyValue {
  param(
    [Parameter(Mandatory = $true)]$Object,
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$Default = ''
  )

  if ($null -eq $Object) { return $Default }
  $property = $Object.PSObject.Properties[$Name]
  if ($null -eq $property -or $null -eq $property.Value) { return $Default }
  return [string]$property.Value
}

function Test-TaskContainsBlockedIntent {
  param([string]$Text)

  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }

  $blockedPatterns = @(
    '(?i)\b(edit|modify|write|rewrite|patch|commit|merge|rebase|push|delete|remove|rename|move)\b',
    '(?i)\b(run|execute|invoke|shell|terminal|powershell|cmd\.exe|bash|script)\b',
    '(?i)\b(deploy|release|publish|production|prod|rollback|migration|database)\b',
    '(?i)\b(secret|credential|password|token|api[ -]?key|private key)\b',
    '(?i)\b(rm\s+-rf|chmod|chown|sudo|curl|wget)\b'
  )

  foreach ($pattern in $blockedPatterns) {
    if ($Text -match $pattern) { return $true }
  }

  return $false
}

function Invoke-LocalRouterPolicy {
  param(
    [Parameter(Mandatory = $true)]$Parsed,
    [Parameter(Mandatory = $true)][string]$TaskText
  )

  $allowedRoutes = @('local', 'amp_initializing', 'premium', 'human_review')
  $allowedRisks = @('low', 'medium', 'high')
  $readOnlyTaskTypes = @('classification', 'summarization', 'routing', 'code_explanation')
  $knownTaskTypes = $readOnlyTaskTypes + @('code_edit', 'security', 'deployment', 'unknown')

  $taskType = Get-JsonPropertyValue -Object $Parsed -Name 'task_type' -Default 'unknown'
  $risk = Get-JsonPropertyValue -Object $Parsed -Name 'risk' -Default 'high'
  $route = Get-JsonPropertyValue -Object $Parsed -Name 'route' -Default 'human_review'
  $reason = Get-JsonPropertyValue -Object $Parsed -Name 'reason' -Default 'No reason returned by local router.'

  if ($knownTaskTypes -notcontains $taskType) {
    $taskType = 'unknown'
  }

  if ($allowedRoutes -notcontains $route) {
    Write-Error "Local router returned unsupported route: $route"
    exit 4
  }

  if ($allowedRisks -notcontains $risk) {
    Write-Error "Local router returned unsupported risk: $risk"
    exit 5
  }

  $blockedIntent = Test-TaskContainsBlockedIntent -Text $TaskText
  $readOnlyType = $readOnlyTaskTypes -contains $taskType
  $localAllowed = ($route -eq 'local' -and $risk -eq 'low' -and $readOnlyType -and -not $blockedIntent)

  $policyReason = 'Local route allowed for read-only low-risk classification, summarization, routing, or code explanation.'

  if ($route -eq 'local' -and -not $localAllowed) {
    if ($risk -ne 'low') {
      $policyReason = 'Local route denied because risk is not low.'
    }
    elseif (-not $readOnlyType) {
      $policyReason = "Local route denied because task_type '$taskType' is not read-only."
    }
    elseif ($blockedIntent) {
      $policyReason = 'Local route denied because the task text appears to request edits, commands, deployment, production access, or secrets.'
    }
    else {
      $policyReason = 'Local route denied by read-only policy.'
    }

    $route = 'human_review'
    $risk = 'high'
  }
  elseif ($route -ne 'local') {
    $policyReason = 'Local route not selected by model; no local execution is enabled.'
  }

  return [pscustomobject]@{
    task_type = $taskType
    risk = $risk
    route = $route
    reason = $reason
    allowed = ($route -ne 'local' -or $localAllowed)
    local_allowed = $localAllowed
    policy_reason = $policyReason
  }
}

if ([string]::IsNullOrWhiteSpace($Task)) {
  Write-Error 'Task is required.'
  exit 2
}

$systemPrompt = @'
You are a local read-only routing model.
Return valid JSON only.
Do not include markdown.
Do not request secrets.
Do not write files.
Do not execute shell commands.
Classify the task and choose a route.

Allowed routes:
- local
- amp_initializing
- premium
- human_review

Schema:
{
  "task_type": "classification|summarization|routing|code_explanation|code_edit|security|deployment|unknown",
  "risk": "low|medium|high",
  "route": "local|amp_initializing|premium|human_review",
  "reason": "short reason",
  "allowed": true
}
'@

try {
  $content = $RouterJson

  if ([string]::IsNullOrWhiteSpace($content)) {
    if ($PolicyOnly) {
      throw 'PolicyOnly requires -RouterJson so no local model call is needed.'
    }

    $body = @{
      model = $Model
      messages = @(
        @{
          role = 'system'
          content = $systemPrompt
        },
        @{
          role = 'user'
          content = $Task
        }
      )
      temperature = 0.1
      max_tokens = 300
    } | ConvertTo-Json -Depth 8

    $response = Invoke-RestMethod `
      -Uri "$BaseUrl/chat/completions" `
      -Method Post `
      -ContentType 'application/json' `
      -Body $body

    $content = $response.choices[0].message.content
  }

  if ([string]::IsNullOrWhiteSpace($content)) {
    throw 'Local router returned an empty response.'
  }

  try {
    $parsed = $content | ConvertFrom-Json
  }
  catch {
    Write-Error "Local router returned invalid JSON: $content"
    exit 3
  }

  $policyResult = Invoke-LocalRouterPolicy -Parsed $parsed -TaskText $Task
  $policyResult | ConvertTo-Json -Depth 8
}
catch {
  Write-Error "Local router failed: $($_.Exception.Message)"
  exit 1
}
