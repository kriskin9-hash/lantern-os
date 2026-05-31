$keys = @('GROQ_API_KEY','OPENROUTER_API_KEY','HF_TOKEN','DEEPSEEK_API_KEY','GEMINI_API_KEY')
foreach ($k in $keys) {
    $v = [Environment]::GetEnvironmentVariable($k)
    $status = if ($v) { "SET (length: $($v.Length))" } else { "NOT SET" }
    Write-Host "$k = $status"
}
