param(
    [switch]$Json
)

$ErrorActionPreference = "Continue"
$checks = New-Object System.Collections.Generic.List[object]

function Add-Check {
    param(
        [string]$Name,
        [ValidateSet("pass", "warn", "fail", "held")]
        [string]$Status,
        [string]$Message,
        [string]$NextAction = ""
    )

    $checks.Add([pscustomobject]@{
        check = $Name
        status = $Status
        message = $Message
        nextAction = $NextAction
    }) | Out-Null

    if (-not $Json) {
        $prefix = @{
            pass = "[PASS]"
            warn = "[WARN]"
            fail = "[FAIL]"
            held = "[HELD]"
        }[$Status]
        Write-Output ("{0} {1}: {2}" -f $prefix, $Name, $Message)
        if ($NextAction) {
            Write-Output ("       Next: {0}" -f $NextAction)
        }
    }
}

function Format-GB {
    param([UInt64]$Bytes)
    return ("{0:N1} GB" -f ($Bytes / 1GB))
}

if (-not $Json) {
    Write-Output "Lantern OS Dual Boot Readiness Validation"
    Write-Output "Mode: read-only Windows inspection"
    Write-Output ""
}

$isAdmin = $false
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
} catch {}

if ($isAdmin) {
    Add-Check "Elevation" "pass" "Running elevated."
} else {
    Add-Check "Elevation" "warn" "Not running elevated; BitLocker, Secure Boot, reagentc, and BCD checks may be incomplete." "Run PowerShell as Administrator for final pre-install validation."
}

try {
    $computerInfo = Get-ComputerInfo
    $firmware = [string]$computerInfo.BiosFirmwareType
    if ($firmware -eq "Uefi" -or $computerInfo.BiosFirmwareType -eq 2) {
        Add-Check "Firmware Mode" "pass" "UEFI detected."
    } else {
        Add-Check "Firmware Mode" "fail" "UEFI was not confirmed. Current value: $firmware" "Enable/verify UEFI mode before Linux dual boot."
    }
    Add-Check "Windows" "pass" "$($computerInfo.OsName) $($computerInfo.OsVersion)"
} catch {
    Add-Check "Firmware Mode" "warn" "Could not read firmware mode: $($_.Exception.Message)" "Verify UEFI in firmware setup."
}

try {
    $secureBoot = Confirm-SecureBootUEFI -ErrorAction Stop
    if ($secureBoot) {
        Add-Check "Secure Boot" "warn" "Secure Boot is enabled." "Use a Secure Boot-compatible NixOS path or disable Secure Boot during install."
    } else {
        Add-Check "Secure Boot" "pass" "Secure Boot is disabled."
    }
} catch {
    Add-Check "Secure Boot" "warn" "Secure Boot status could not be read without elevation or firmware support." "Check Secure Boot in firmware setup or rerun elevated."
}

$disks = @()
try {
    $disks = @(Get-Disk)
    foreach ($disk in $disks) {
        if ($disk.PartitionStyle -eq "GPT") {
            Add-Check "Disk $($disk.Number) Partition Style" "pass" "$($disk.FriendlyName): GPT, $([math]::Round($disk.Size / 1GB)) GB, $($disk.HealthStatus)."
        } else {
            Add-Check "Disk $($disk.Number) Partition Style" "warn" "$($disk.FriendlyName): $($disk.PartitionStyle)." "Prefer GPT/UEFI for clean dual boot."
        }
    }
} catch {
    Add-Check "Disk Inventory" "fail" "Could not inspect disks: $($_.Exception.Message)" "Resolve disk inspection before install."
}

try {
    $volumes = @(Get-Volume | Where-Object { $_.DriveType -eq "Fixed" -and $_.DriveLetter })
    $shrinkCandidates = @($volumes | Where-Object { $_.SizeRemaining -ge 100GB })
    $minimumCandidates = @($volumes | Where-Object { $_.SizeRemaining -ge 50GB })

    foreach ($volume in $volumes) {
        Add-Check "Volume $($volume.DriveLetter): Free Space" "pass" ("{0} free of {1}" -f (Format-GB $volume.SizeRemaining), (Format-GB $volume.Size))
    }

    if ($shrinkCandidates.Count -gt 0) {
        $names = ($shrinkCandidates | ForEach-Object { "$($_.DriveLetter):" }) -join ", "
        Add-Check "Shrink Candidate" "pass" "At least one volume has 100GB+ free: $names." "Shrink one candidate in Disk Management to create unallocated space."
    } elseif ($minimumCandidates.Count -gt 0) {
        $names = ($minimumCandidates | ForEach-Object { "$($_.DriveLetter):" }) -join ", "
        Add-Check "Shrink Candidate" "warn" "At least one volume has 50GB+ free: $names, but 100GB+ is recommended." "Free more space or accept a smaller NixOS install."
    } else {
        Add-Check "Shrink Candidate" "fail" "No fixed volume has 50GB+ free." "Free space before attempting dual boot."
    }
} catch {
    Add-Check "Volume Free Space" "warn" "Could not inspect volumes: $($_.Exception.Message)" "Check free space manually."
}

try {
    $partitions = @(Get-Partition)
    $efi = @($partitions | Where-Object { $_.Type -eq "System" -or "$($_.GptType)" -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}" })
    if ($efi.Count -gt 0) {
        Add-Check "EFI System Partition" "pass" "EFI partition present."
    } else {
        Add-Check "EFI System Partition" "fail" "No EFI System Partition found." "Do not proceed until EFI boot layout is understood."
    }

    $unallocated = 0
    foreach ($disk in $disks) {
        $parts = @($partitions | Where-Object { $_.DiskNumber -eq $disk.Number })
        $used = ($parts | Measure-Object -Property Size -Sum).Sum
        if ($null -eq $used) { $used = 0 }
        $gap = [UInt64]([Math]::Max(0, [double]$disk.Size - [double]$used))
        $unallocated += $gap
    }

    if ($unallocated -ge 50GB) {
        Add-Check "Unallocated Install Space" "pass" ("{0} unallocated." -f (Format-GB $unallocated))
    } else {
        Add-Check "Unallocated Install Space" "warn" ("Only {0} unallocated. Windows is dual-boot-capable, but the Linux installer will need unallocated space." -f (Format-GB $unallocated)) "Shrink D: or C: from Windows Disk Management before installing NixOS."
    }
} catch {
    Add-Check "Partition Layout" "warn" "Could not fully inspect partitions: $($_.Exception.Message)" "Review Disk Management manually."
}

try {
    if ($isAdmin) {
        $bitlocker = @(Get-BitLockerVolume -ErrorAction Stop)
        $protected = @($bitlocker | Where-Object { $_.ProtectionStatus -eq "On" })
        if ($protected.Count -gt 0) {
            Add-Check "BitLocker" "warn" "BitLocker protection is on for: $(( $protected | ForEach-Object { $_.MountPoint }) -join ', ')." "Back up recovery keys and suspend/disable before partition changes."
        } else {
            Add-Check "BitLocker" "pass" "No enabled BitLocker protection detected."
        }
    } else {
        Add-Check "BitLocker" "warn" "Not checked because this shell is not elevated." "Run elevated and back up recovery keys before partition changes."
    }
} catch {
    Add-Check "BitLocker" "warn" "Could not determine BitLocker status: $($_.Exception.Message)" "Verify encryption/recovery keys before partition changes."
}

Add-Check "Physical Install Boundary" "held" "The actual OS install, partition shrink, bootloader choice, and reboot must be done by the operator at the keyboard." "Use dual-boot/INSTALL-CHECKLIST.md."

$failed = @($checks | Where-Object { $_.status -eq "fail" }).Count
$warnings = @($checks | Where-Object { $_.status -eq "warn" }).Count
$passes = @($checks | Where-Object { $_.status -eq "pass" }).Count
$held = @($checks | Where-Object { $_.status -eq "held" }).Count
$readyForPrep = ($failed -eq 0)
$readyForInstall = ($failed -eq 0 -and @($checks | Where-Object { $_.check -eq "Unallocated Install Space" -and $_.status -eq "pass" }).Count -gt 0)

$result = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    readyForPrep = $readyForPrep
    readyForInstall = $readyForInstall
    pass = $passes
    warn = $warnings
    fail = $failed
    held = $held
    checks = $checks
    summary = if ($readyForInstall) {
        "Ready for installer preparation, with operator-held physical actions."
    } elseif ($readyForPrep) {
        "PC is dual-boot-capable, but install space is not prepared yet."
    } else {
        "Not ready; resolve failed checks first."
    }
}

if ($Json) {
    $result | ConvertTo-Json -Depth 8
} else {
    Write-Output ""
    Write-Output "Summary"
    Write-Output ("PASS={0} WARN={1} FAIL={2} HELD={3}" -f $passes, $warnings, $failed, $held)
    Write-Output ("Ready for prep:    {0}" -f $readyForPrep)
    Write-Output ("Ready for install: {0}" -f $readyForInstall)
    Write-Output $result.summary
}

if ($failed -gt 0) { exit 1 }
exit 0
