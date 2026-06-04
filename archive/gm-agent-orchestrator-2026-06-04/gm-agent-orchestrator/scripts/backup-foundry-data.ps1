#!/usr/bin/env powershell
<#
.SYNOPSIS
Backup Lantern and Foundry data to cloud-synced location (Dropbox/OneDrive/Google Drive).

.DESCRIPTION
Backs up ~/.lantern/families/ and ~/.foundry/ directories to a cloud-synced folder.
Preserves directory structure. Runs hourly via scheduled task.

.EXAMPLE
.\backup-foundry-data.ps1 -CloudPath "C:\Users\alexp\Dropbox\Backups\Lantern-Foundry"

.NOTES
Cloud path must already be synced with cloud provider (Dropbox, OneDrive, or Google Drive).
Logs to $CloudPath\backup.log
#>

param(
    [string]$CloudPath = "C:\Users\alexp\Dropbox\Backups\Lantern-Foundry"
)

$ErrorActionPreference = "SilentlyContinue"

# Paths to backup
$LanternPath = "$env:USERPROFILE\.lantern"
$FoundryPath = "$env:USERPROFILE\.foundry"
$BackupLog = Join-Path $CloudPath "backup.log"

# Create cloud backup directory if it doesn't exist
if (-not (Test-Path $CloudPath)) {
    New-Item -ItemType Directory -Path $CloudPath -Force | Out-Null
    Add-Content $BackupLog "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Created backup directory: $CloudPath"
}

# Backup function
function Backup-Directory {
    param(
        [string]$SourcePath,
        [string]$DestName
    )

    if (-not (Test-Path $SourcePath)) {
        Add-Content $BackupLog "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ⚠ Source not found: $SourcePath"
        return
    }

    $DestPath = Join-Path $CloudPath $DestName

    # Remove old backup if exists
    if (Test-Path $DestPath) {
        Remove-Item $DestPath -Recurse -Force
    }

    # Copy directory
    Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force

    $FileCount = (Get-ChildItem $DestPath -Recurse | Measure-Object).Count
    Add-Content $BackupLog "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ✅ Backed up $DestName ($FileCount items)"
}

# Execute backups
Add-Content $BackupLog "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] === Backup started ==="

Backup-Directory -SourcePath $LanternPath -DestName "lantern-state"
Backup-Directory -SourcePath $FoundryPath -DestName "foundry-data"

Add-Content $BackupLog "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] === Backup completed ==="

# Keep log trimmed to last 100 lines
if ((Get-Content $BackupLog | Measure-Object -Line).Lines -gt 100) {
    $LastLines = Get-Content $BackupLog | Select-Object -Last 100
    Set-Content $BackupLog $LastLines
}
