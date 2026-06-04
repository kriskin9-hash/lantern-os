[CmdletBinding()]
param(
    [ValidateSet("propose","validate","promote","rollback")]
    [string]$Action = "validate",

    [string]$Root = "",
    [string]$PatchId = "",
    [string]$TargetPath = "",
    [string]$ContentPath = "",
    [string]$BackupPath = "",
    [string]$Reason = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-Result {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$ErrorMessage = "",
        [hashtable]$Extra = @{}
    )

    $obj = [ordered]@{
        ok = $Ok
        state = $State
        action = $Action
        patch_id = $PatchId
        target_path = $TargetPath
        backup_path = $BackupPath
        dry_run = [bool]$DryRun
        error = $ErrorMessage
        generated_at = (Get-Date).ToString("o")
    }

    foreach ($key in $Extra.Keys) {
        $obj[$key] = $Extra[$key]
    }

    [pscustomobject]$obj
}

function Resolve-RepoPath {
    param([string]$RepoRoot, [string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { throw "Path is required" }

    $rootFull = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    if ([string]::IsNullOrWhiteSpace($rootFull)) { throw "Repository root resolved to an empty path." }

    if ([System.IO.Path]::IsPathRooted($Path)) {
        $resolved = [System.IO.Path]::GetFullPath($Path)
    }
    else {
        $resolved = [System.IO.Path]::GetFullPath((Join-Path $rootFull $Path))
    }

    $rootWithSeparator = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    $isRoot = [string]::Equals($resolved, $rootFull, [System.StringComparison]::OrdinalIgnoreCase)
    $isChild = $resolved.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)
    if (-not ($isRoot -or $isChild)) {
        throw "Refusing path outside repo root: $resolved"
    }

    return $resolved
}

function Get-JsonProperty {
    param([object]$Object, [string]$Name, $Default = $null)
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

try {
    if ([string]::IsNullOrWhiteSpace($Root)) {
        $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    if (!(Test-Path -LiteralPath $Root -PathType Container)) {
        throw "Missing root: $Root"
    }

    $Root = [System.IO.Path]::GetFullPath($Root)
    $stageRoot = Join-Path $Root ".patch-staging"
    $auditRoot = Join-Path $Root "logs\control-actions"

    if (!$DryRun) {
        New-Item -ItemType Directory -Force -Path $stageRoot,$auditRoot | Out-Null
    }

    switch ($Action) {
        "propose" {
            if ([string]::IsNullOrWhiteSpace($TargetPath)) { throw "TargetPath is required" }
            if ([string]::IsNullOrWhiteSpace($ContentPath)) { throw "ContentPath is required" }
            if (!(Test-Path -LiteralPath $ContentPath -PathType Leaf)) { throw "Missing ContentPath: $ContentPath" }

            if ([string]::IsNullOrWhiteSpace($PatchId)) {
                $PatchId = "patch-" + (Get-Date -Format "yyyyMMdd-HHmmss")
            }

            $patchDir = Join-Path $stageRoot $PatchId
            $metadataPath = Join-Path $patchDir "metadata.json"
            $payloadPath = Join-Path $patchDir "payload.ps1"

            if (!$DryRun) {
                New-Item -ItemType Directory -Force -Path $patchDir | Out-Null
                Copy-Item -LiteralPath $ContentPath -Destination $payloadPath -Force

                [pscustomobject]@{
                    patch_id = $PatchId
                    target_path = $TargetPath
                    content_path = $ContentPath
                    payload_path = $payloadPath
                    reason = $Reason
                    created_at = (Get-Date).ToString("o")
                } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $metadataPath -Encoding UTF8
            }

            $result = New-Result -Ok $true -State "proposed" -Extra @{
                stage_root = $stageRoot
                metadata_path = $metadataPath
                payload_path = $payloadPath
            }
        }

        "validate" {
            if ([string]::IsNullOrWhiteSpace($PatchId)) { throw "PatchId is required" }

            $patchDir = Join-Path $stageRoot $PatchId
            $metadataPath = Join-Path $patchDir "metadata.json"
            $payloadPath = Join-Path $patchDir "payload.ps1"

            if (!(Test-Path -LiteralPath $metadataPath -PathType Leaf)) { throw "Missing staged metadata: $metadataPath" }
            if (!(Test-Path -LiteralPath $payloadPath -PathType Leaf)) { throw "Missing staged payload: $payloadPath" }

            $tokens = $null
            $errors = $null
            [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $payloadPath), [ref]$tokens, [ref]$errors) | Out-Null
            if ($errors.Count -gt 0) {
                throw "Parser failed: " + (($errors | ForEach-Object { $_.Message }) -join "; ")
            }

            $result = New-Result -Ok $true -State "validated" -Extra @{
                metadata_path = $metadataPath
                payload_path = $payloadPath
            }
        }

        "promote" {
            if ([string]::IsNullOrWhiteSpace($PatchId)) { throw "PatchId is required" }

            $patchDir = Join-Path $stageRoot $PatchId
            $metadataPath = Join-Path $patchDir "metadata.json"
            $payloadPath = Join-Path $patchDir "payload.ps1"

            if (!(Test-Path -LiteralPath $metadataPath -PathType Leaf)) { throw "Missing staged metadata: $metadataPath" }
            if (!(Test-Path -LiteralPath $payloadPath -PathType Leaf)) { throw "Missing staged payload: $payloadPath" }

            $metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
            $target = Resolve-RepoPath -RepoRoot $Root -Path ([string]$metadata.target_path)
            $targetDir = Split-Path -Parent $target
            if (Test-Path -LiteralPath $target -PathType Container) { throw "Refusing to promote over a directory: $target" }
            $targetExisted = Test-Path -LiteralPath $target -PathType Leaf
            $backup = if ($targetExisted) { $target + ".bak-" + (Get-Date -Format "yyyyMMdd-HHmmss") } else { "" }

            if ($DryRun) {
                $result = New-Result -Ok $true -State "promote_dry_run" -Extra @{
                    target = $target
                    target_existed = [bool]$targetExisted
                    backup = $backup
                }
                break
            }

            if (!(Test-Path -LiteralPath $targetDir -PathType Container)) {
                New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
            }

            if ($targetExisted) {
                Copy-Item -LiteralPath $target -Destination $backup -Force
            }

            Copy-Item -LiteralPath $payloadPath -Destination $target -Force

            $auditPath = Join-Path $auditRoot ("$PatchId-promote.json")
            [pscustomobject]@{
                ok = $true
                action = "promote_powershell_patch"
                patch_id = $PatchId
                target = $target
                target_existed = [bool]$targetExisted
                backup = $backup
                promoted_at = (Get-Date).ToString("o")
            } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $auditPath -Encoding UTF8

            $result = New-Result -Ok $true -State "promoted" -Extra @{
                target = $target
                target_existed = [bool]$targetExisted
                backup = $backup
                audit_path = $auditPath
            }
        }

        "rollback" {
            if ([string]::IsNullOrWhiteSpace($PatchId)) { throw "PatchId is required" }

            $promoteAudit = Join-Path $auditRoot ("$PatchId-promote.json")
            if (!(Test-Path -LiteralPath $promoteAudit -PathType Leaf)) {
                throw "Missing promotion audit for rollback: $promoteAudit"
            }

            $audit = Get-Content -LiteralPath $promoteAudit -Raw | ConvertFrom-Json
            $target = Resolve-RepoPath -RepoRoot $Root -Path ([string]$audit.target)
            $targetExisted = [bool](Get-JsonProperty -Object $audit -Name "target_existed" -Default $true)
            $backup = if ([string]::IsNullOrWhiteSpace($BackupPath)) { [string](Get-JsonProperty -Object $audit -Name "backup" -Default "") } else { Resolve-RepoPath -RepoRoot $Root -Path $BackupPath }

            if ($targetExisted) {
                if ([string]::IsNullOrWhiteSpace($backup)) { throw "No backup path found for patch $PatchId" }
                $backup = Resolve-RepoPath -RepoRoot $Root -Path $backup
                if (!(Test-Path -LiteralPath $backup -PathType Leaf)) { throw "Missing rollback backup: $backup" }
            }
            elseif (-not [string]::IsNullOrWhiteSpace($BackupPath)) {
                throw "BackupPath override is invalid because promotion created a new target instead of backing up an existing file."
            }

            if ($DryRun) {
                $result = New-Result -Ok $true -State "rollback_dry_run" -Extra @{
                    target = $target
                    target_existed = [bool]$targetExisted
                    backup = $backup
                    operation = $(if ($targetExisted) { "restore_backup" } else { "delete_created_target" })
                    promote_audit = $promoteAudit
                }
                break
            }

            if ($targetExisted) {
                Copy-Item -LiteralPath $backup -Destination $target -Force
                $operation = "restore_backup"
            }
            else {
                if (Test-Path -LiteralPath $target -PathType Container) { throw "Refusing to remove directory during rollback: $target" }
                if (Test-Path -LiteralPath $target -PathType Leaf) { Remove-Item -LiteralPath $target -Force }
                $operation = "delete_created_target"
            }

            $rollbackAudit = Join-Path $auditRoot ("$PatchId-rollback.json")
            [pscustomobject]@{
                ok = $true
                action = "rollback_last_mcp_promotion"
                patch_id = $PatchId
                target = $target
                target_existed = [bool]$targetExisted
                backup = $backup
                operation = $operation
                promote_audit = $promoteAudit
                rolled_back_at = (Get-Date).ToString("o")
            } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $rollbackAudit -Encoding UTF8

            $result = New-Result -Ok $true -State "rolled_back" -Extra @{
                target = $target
                target_existed = [bool]$targetExisted
                backup = $backup
                operation = $operation
                promote_audit = $promoteAudit
                audit_path = $rollbackAudit
            }
        }
    }
}
catch {
    $result = New-Result -Ok $false -State "error" -ErrorMessage $_.Exception.Message
}

$result | ConvertTo-Json -Depth 20
