$script = Get-Content 'd:\tmp\lantern-os\scripts\Invoke-OllamaAgent.ps1' -Raw
$errors = @()
$null = [System.Management.Automation.PSParser]::Tokenize($script, [ref]$errors)
Write-Host ('Errors: ' + $errors.Count)
if ($errors.Count -eq 0) { Write-Host 'SYNTAX OK' } else { $errors | ForEach-Object { Write-Host ($_.Message + ' at line ' + $_.Token.StartLine) } }
