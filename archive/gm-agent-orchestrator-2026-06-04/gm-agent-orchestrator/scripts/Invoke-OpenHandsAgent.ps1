[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$env:OPENHANDS_SUPPRESS_BANNER = "1"
$env:PYTHONWARNINGS = "ignore"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

function ConvertTo-ProcessArgumentString {
    param([string[]]$Arguments)

    $escaped = foreach ($argument in @($Arguments)) {
        if ($null -eq $argument) { continue }

        $text = [string]$argument
        if ($text -eq "") {
            '""'
            continue
        }

        if ($text -notmatch '[\s"]') {
            $text
            continue
        }

        '"' + ($text -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
    }

    return ($escaped -join ' ')
}

function Normalize-OpenHandsArgs {
    param([string[]]$InputArgs)

    if ($null -eq $InputArgs -or $InputArgs.Count -eq 0) {
        return @()
    }

    $normalized = New-Object System.Collections.Generic.List[string]
    $i = 0
    while ($i -lt $InputArgs.Count) {
        $current = [string]$InputArgs[$i]
        if (($current -eq "-t" -or $current -eq "--task") -and ($i + 1) -lt $InputArgs.Count) {
            [void]$normalized.Add($current)
            $taskTail = @($InputArgs[($i + 1)..($InputArgs.Count - 1)])
            [void]$normalized.Add(($taskTail -join " "))
            break
        }

        [void]$normalized.Add($current)
        $i++
    }

    return @($normalized)
}

$python312 = "C:\Users\alexp\AppData\Local\Programs\Python\Python312\python.exe"

if (!(Test-Path -LiteralPath $python312 -PathType Leaf)) {
    Write-Error "OpenHands wrapper requires Python 3.12 at '$python312'. Install/restore Python 3.12 or update scripts\Invoke-OpenHandsAgent.ps1 to the durable uv-enabled interpreter path."
    exit 127
}

# Run through Start-Process with explicit capture so native stderr text remains
# plain text instead of being promoted into PowerShell error records.
$temp = [System.IO.Path]::GetTempFileName()
$stdoutPath = "$temp.out"
$stderrPath = "$temp.err"
$exitCode = 1

try {
    $normalizedArgs = Normalize-OpenHandsArgs -InputArgs @($Args)
    $openhandsArgs = @("-m", "uv", "tool", "run", "openhands")
    if (-not (@($normalizedArgs) -contains "--override-with-envs")) {
        $openhandsArgs += "--override-with-envs"
    }
    if ($normalizedArgs.Count -gt 0) {
        $openhandsArgs += @($normalizedArgs)
    }

    $process = Start-Process -FilePath $python312 `
        -ArgumentList (ConvertTo-ProcessArgumentString -Arguments $openhandsArgs) `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath

    $process.WaitForExit()
    $exitCode = $process.ExitCode

    if (Test-Path -LiteralPath $stdoutPath -PathType Leaf) {
        $stdout = Get-Content -LiteralPath $stdoutPath -Raw
        if (-not [string]::IsNullOrWhiteSpace($stdout)) {
            $stdout -split "`r?`n" | ForEach-Object {
                if (-not [string]::IsNullOrWhiteSpace($_)) {
                    Write-Output $_
                }
            }
        }
    }

    if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
        $stderr = Get-Content -LiteralPath $stderrPath -Raw
        if (-not [string]::IsNullOrWhiteSpace($stderr)) {
            # Emit stderr lines to stdout intentionally so upstream slot logic
            # can classify failures by exit code and message content.
            $stderr -split "`r?`n" | ForEach-Object {
                if (-not [string]::IsNullOrWhiteSpace($_)) {
                    Write-Output $_
                }
            }
        }
    }
}
finally {
    Remove-Item -LiteralPath $temp, $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
}

exit $exitCode
