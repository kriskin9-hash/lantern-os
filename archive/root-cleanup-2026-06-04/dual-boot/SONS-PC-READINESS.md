# Son's PC Dual-Boot Readiness

Status: candidate, read-only prep only.

This is the second PC dual-boot track. Do not assume the primary PC readiness
applies to this machine.

## Read-Only Checks

Run on son's PC from PowerShell:

```powershell
Get-ComputerInfo | Select-Object CsName, OsName, BiosFirmwareType, CsProcessors, CsTotalPhysicalMemory
Get-Disk | Select-Object Number, FriendlyName, PartitionStyle, OperationalStatus, Size
Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem, Size, SizeRemaining
Confirm-SecureBootUEFI
reagentc /info
```

If copied to that machine, also run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\dual-boot\Test-DualBootReadiness.ps1 -Json
```

## Gates

| Gate | Required Evidence | Status |
|---|---|---|
| backup complete | operator confirms current backup | pending |
| UEFI/GPT | read-only disk and firmware output | pending |
| free or unallocated space | volume/disk output | pending |
| BitLocker known | manage-bde or settings screenshot | pending |
| Secure Boot known | `Confirm-SecureBootUEFI` | pending |
| recovery path known | Windows recovery + installer media | pending |

## Boundary

No partition resizing, formatting, BCD edits, firmware boot order changes, or
OS installation are performed by automation. Physical install remains operator
controlled.
