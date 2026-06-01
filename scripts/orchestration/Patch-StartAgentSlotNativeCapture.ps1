[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function New-Result {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$ErrorMessage = "",
        [hashtable]$Extra = @{}
    )

    $payload = [ordered]@{
        ok = $Ok
        state = $State
        dryRun = [bool]$DryRun
        error = $ErrorMessage
        generatedAt = (Get-Date).ToString("o")
    }

    foreach ($key in $Extra.Keys) { $payload[$key] = $Extra[$key] }
    [pscustomobject]$payload
}

try {
    $target = Join-Path $Root "scripts\Start-AgentSlot.ps1"
    if (!(Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing target: $target" }

    $text = Get-Content -LiteralPath $target -Raw -ErrorAction Stop
    if ($text -match "function Invoke-NativeCommandCaptured") {
        $result = New-Result -Ok $true -State "already_patched" -Extra @{ target = $target }
    }
    else {
        $insertAfter = @'
function Invoke-CheckedProbe {
    param(
        [Parameter(Mandatory = $true)] [string]$Exe,
        [Parameter(Mandatory = $true)] [string[]]$Args,
        [int]$TimeoutSeconds = 15
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $out = "$temp.out"
    $err = "$temp.err"

    try {
        $p = Start-Process -FilePath $Exe -ArgumentList $Args -NoNewWindow -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
        $done = $p.WaitForExit($TimeoutSeconds * 1000)
        
        $stdout = if (Test-Path $out) { Get-Content $out -Raw } else { "" }
        $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }
        $exitCode = if ($done) { $p.ExitCode } else { try { $p.Kill() } catch {}; $null }

        return [pscustomobject]@{
            exitCode = $exitCode
            timedOut = -not $done
            stdout   = $stdout
            stderr   = $stderr
            combined = ("$stdout`n$stderr").Trim()
        }
    }
    finally {
        Remove-Item -Path $temp, $out, $err -Force -ErrorAction SilentlyContinue
    }
}
'@

        $nativeCapture = @'

function Invoke-NativeCommandCaptured {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(Mandatory = $true)][string[]]$Args,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [int]$TimeoutSeconds = 0
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $out = "$temp.out"
    $err = "$temp.err"

    try {
        $process = Start-Process -FilePath $Exe `
            -ArgumentList $Args `
            -WorkingDirectory $WorkingDirectory `
            -NoNewWindow `
            -PassThru `
            -RedirectStandardOutput $out `
            -RedirectStandardError $err

        if ($TimeoutSeconds -gt 0) {
            $done = $process.WaitForExit($TimeoutSeconds * 1000)
            if (-not $done) {
                try { $process.Kill() } catch {}
                $stdout = if (Test-Path $out) { Get-Content $out -Raw } else { "" }
                $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }
                return [pscustomobject]@{
                    exitCode = $null
                    timedOut = $true
                    stdout = $stdout
                    stderr = $stderr
                    combined = ("$stdout`n$stderr").Trim()
                }
            }
        }
        else {
            $process.WaitForExit()
        }

        $stdout = if (Test-Path $out) { Get-Content $out -Raw } else { "" }
        $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }

        return [pscustomobject]@{
            exitCode = $process.ExitCode
            timedOut = $false
            stdout = $stdout
            stderr = $stderr
            combined = ("$stdout`n$stderr").Trim()
        }
    }
    finally {
        Remove-Item -Path $temp, $out, $err -Force -ErrorAction SilentlyContinue
    }
}

function Add-OutputBlockToLog {
    param(
        [Parameter(Mandatory = $true)][string]$LogFile,
        [string]$Label,
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Text)) { return }
    Add-LogLine -Path $LogFile -Message "`n----- $Label -----"
    foreach ($line in ($Text -split "`r?`n")) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            Add-LogLine -Path $LogFile -Message $line
            if (-not $Headless) { Write-Host $line }
        }
    }
}
'@

        if (-not $text.Contains($insertAfter)) {
            throw "Could not find Invoke-CheckedProbe block to insert native capture helper."
        }

        $text = $text.Replace($insertAfter, $insertAfter + $nativeCapture)

        $pattern = '(?s)function Invoke-Agent \{.*?\n\}\r?\n\r?\nfunction Invoke-ValidationCommand'
        $replacement = @'
function Invoke-Agent {
    param(
        [bool]$Resume,
        [string]$LogFile
    )

    $slotRole = Get-SlotRole
    $prompt = "Read AGENT_RESUME.md and TASK_QUEUE.md. You are slot '$script:SlotName' with role '$slotRole'. Use the role only to guide execution style; it does not expand scope or delegation authority. Continue only the assigned task. Use local GameMaker tooling when helpful. Do not ask permission unless blocked. Split work into small commits, validate, update AGENT_LOG.md, then stop after one completed task or one failed validation cycle."
    $cmdSpec = Get-AgentCommandSpec -Resume:$Resume

    if ($cmdSpec.Count -lt 1) {
        throw "Agent command spec is empty for slot $script:SlotName."
    }

    $exe = [string]$cmdSpec[0]
    $args = @()

    for ($i = 1; $i -lt $cmdSpec.Count; $i++) {
        $args += ([string]$cmdSpec[$i]).Replace("{prompt}", $prompt)
    }

    if (!(Get-Command $exe -ErrorAction SilentlyContinue)) {
        throw "Agent executable not found on PATH: $exe"
    }

    Add-LogLine -Path $LogFile -Message "`n===== $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") $exe $($args -join ' ') ====="

    $result = Invoke-NativeCommandCaptured -Exe $exe -Args $args -WorkingDirectory $WorktreePath
    Add-OutputBlockToLog -LogFile $LogFile -Label "stdout" -Text ([string]$result.stdout)
    Add-OutputBlockToLog -LogFile $LogFile -Label "stderr" -Text ([string]$result.stderr)

    if ($result.timedOut) {
        return @{
            ExitCode = 124
            Output = [string]$result.combined
            ErrorMessage = "Agent process timed out"
        }
    }

    return @{
        ExitCode = [int]$result.exitCode
        Output = [string]$result.combined
        ErrorMessage = Extract-ErrorMessage -Output ([string]$result.combined)
    }
}

function Invoke-ValidationCommand
'@

        $newText = [regex]::Replace($text, $pattern, $replacement, 1)
        if ($newText -eq $text) { throw "Could not replace Invoke-Agent block." }

        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseInput($newText, [ref]$tokens, [ref]$errors) | Out-Null
        if ($errors.Count -gt 0) {
            throw "Patched Start-AgentSlot.ps1 parser failed: " + (($errors | ForEach-Object { $_.Message }) -join "; ")
        }

        if ($DryRun) {
            $result = New-Result -Ok $true -State "patch_dry_run" -Extra @{ target = $target }
        }
        else {
            $backup = $target + ".bak-native-capture-" + (Get-Date -Format "yyyyMMdd-HHmmss")
            Copy-Item -LiteralPath $target -Destination $backup -Force
            [System.IO.File]::WriteAllText($target, $newText, [System.Text.UTF8Encoding]::new($false))
            $result = New-Result -Ok $true -State "patched" -Extra @{ target = $target; backup = $backup }
        }
    }
}
catch {
    $result = New-Result -Ok $false -State "error" -ErrorMessage $_.Exception.Message
}

$result | ConvertTo-Json -Depth 20
