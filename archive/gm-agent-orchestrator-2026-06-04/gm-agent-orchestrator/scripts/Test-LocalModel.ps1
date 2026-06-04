param(
  [string]$BaseUrl = $(if ($env:LOCAL_LLM_BASE_URL) { $env:LOCAL_LLM_BASE_URL } else { 'http://localhost:1234/v1' }),
  [string]$Model = $(if ($env:LOCAL_LLM_MODEL) { $env:LOCAL_LLM_MODEL } else { 'lfm2-24b-a2b' })
)

$ErrorActionPreference = 'Stop'

$body = @{
  model = $Model
  messages = @(
    @{
      role = 'system'
      content = 'You are a local routing model. Return concise JSON only.'
    },
    @{
      role = 'user'
      content = 'Classify this task: summarize a failing test log. Return JSON with task_type, risk, and route.'
    }
  )
  temperature = 0.1
  max_tokens = 200
} | ConvertTo-Json -Depth 8

try {
  $response = Invoke-RestMethod `
    -Uri "$BaseUrl/chat/completions" `
    -Method Post `
    -ContentType 'application/json' `
    -Body $body

  $content = $response.choices[0].message.content

  if ([string]::IsNullOrWhiteSpace($content)) {
    throw 'Local model returned an empty response.'
  }

  $content
}
catch {
  Write-Error "Local model smoke test failed: $($_.Exception.Message)"
  exit 1
}
