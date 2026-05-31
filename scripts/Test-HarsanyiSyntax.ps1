$script = Get-Content 'd:\tmp\lantern-os\skills\trade\Harsanyi-TypeSpace.ps1' -Raw
$errors = @()
$null = [System.Management.Automation.PSParser]::Tokenize($script, [ref]$errors)
Write-Host ('Errors found: ' + $errors.Count)
if ($errors.Count -eq 0) { Write-Host 'SYNTAX OK' } else { $errors | ForEach-Object { Write-Host ($_.Message + ' at line ' + $_.Token.StartLine) } }
