$script:BaseGetToolsListForStrictSafePowerShell = (Get-Command Get-ToolsList -CommandType Function).ScriptBlock

function Invoke-SafePowerShellRunnerTool {
    param([object]$Arguments)

    if ($null -eq $Arguments -or [string]::IsNullOrWhiteSpace([string]$Arguments.script_name)) { throw "Missing required argument: script_name" }
    $scriptName = [string]$Arguments.script_name

    $args = @("-Root", $Root, "-ScriptName", $scriptName)

    $argumentJson = Get-OptionalJsonProperty -Object $Arguments -Name "argument_json"
    $argumentJsonBase64 = Get-OptionalJsonProperty -Object $Arguments -Name "argument_json_base64"
    $rawArguments = Get-OptionalJsonProperty -Object $Arguments -Name "arguments"
    $dryRun = Get-OptionalJsonProperty -Object $Arguments -Name "dry_run"
    $planOnly = Get-OptionalJsonProperty -Object $Arguments -Name "plan_only"
    $timeoutSeconds = Get-OptionalJsonProperty -Object $Arguments -Name "timeout_seconds"

    if (-not [string]::IsNullOrWhiteSpace([string]$argumentJson)) { $args += @("-ArgumentJson", [string]$argumentJson) }
    elseif (-not [string]::IsNullOrWhiteSpace([string]$argumentJsonBase64)) { $args += @("-ArgumentJsonBase64", [string]$argumentJsonBase64) }
    elseif ($null -ne $rawArguments) { $args += @("-ArgumentJson", (ConvertTo-Json -InputObject @($rawArguments) -Depth 80 -Compress)) }
    if ($true -eq [bool]$dryRun) { $args += "-DryRun" }
    if ($true -eq [bool]$planOnly) { $args += "-PlanOnly" }
    if ($null -ne $timeoutSeconds) { $args += @("-TimeoutSeconds", [string]$timeoutSeconds) }

    return Invoke-JsonScript -ScriptPath $SafePowerShellRunnerScript -Arguments $args
}

function Get-StrictRunSafePowerShellSchema {
    return [pscustomobject]@{
        type = "object"
        additionalProperties = $false
        properties = [pscustomobject]@{
            script_name = [pscustomobject]@{
                type = "string"
                description = "Allowlisted PowerShell helper script basename, for example Get-OrchestratorStatus.ps1."
            }
            argument_json = [pscustomobject]@{
                type = "string"
                description = "JSON array string of helper arguments. Use [] when no arguments are needed."
            }
            dry_run = [pscustomobject]@{
                type = "boolean"
                description = "Whether to append -DryRun for helpers that support it."
            }
            plan_only = [pscustomobject]@{
                type = "boolean"
                description = "Whether to append -PlanOnly for helpers that support it."
            }
            timeout_seconds = [pscustomobject]@{
                type = "integer"
                minimum = 1
                maximum = 600
                description = "Maximum helper runtime in seconds."
            }
        }
        required = @("script_name", "argument_json", "dry_run", "plan_only", "timeout_seconds")
    }
}

function Get-ToolsList {
    $result = & $script:BaseGetToolsListForStrictSafePowerShell
    foreach ($tool in @($result.tools)) {
        if ([string]$tool.name -eq "run_safe_powershell") {
            $tool.inputSchema = Get-StrictRunSafePowerShellSchema
        }
    }
    return $result
}
