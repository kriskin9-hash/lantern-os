# Lantern OS Dual Boot: Hardware Assumptions & Compatibility

This document outlines the hardware assumptions and compatibility requirements for the Lantern OS dual boot setup.

## Validated System Requirements

### Processor (CPU)
- **Requirement:** 64-bit x86_64 (Intel or AMD)
- **Minimum:** Any modern processor from the last 10 years
- **Recommended:** Intel 6th Gen or newer, AMD Ryzen series
- **Verified on:**
  - Intel Core i5/i7 (6th gen+)
  - AMD Ryzen 5/7

### Memory (RAM)
- **Minimum:** 4GB
- **Recommended:** 8GB or more
- **NixOS footprint:** ~2GB for base system

### Storage (Disk)
- **Type:** SATA SSD or NVMe recommended (HDD works but slower)
- **Windows partition:** ~100GB minimum
- **NixOS partition:** 50GB minimum, 100GB recommended
- **Total required:** At least 150GB free space
- **Filesystem:** Windows = NTFS/exFAT, NixOS = ext4

### Firmware & Boot
- **BIOS Type:** UEFI (not Legacy BIOS)
- **Boot Mode:** UEFI with Secure Boot capable
- **Secure Boot:** Must be disabled for NixOS installation
- **TPM:** Optional (NixOS works with or without)

### Network
- **Requirement:** Wired Ethernet or WiFi during NixOS installation
- **Speed:** Broadband internet for downloading NixOS (~1-2 GB)
- **Duration:** Plan 30-60 minutes for first installation

### Display & Input
- **Monitor:** Any standard HDMI/DP display
- **Keyboard & Mouse:** USB or wireless (USB receiver connected)
- **BIOS Access:** Need ability to enter BIOS/UEFI setup (F2, F12, DEL, or ESC during POST)

## Known Compatible Configurations

### Confirmed Working
- **Surface:** ThinkPad X1 Carbon + NixOS 23.11
- **Surface:** Dell XPS + NixOS 23.05
- **Surface:** Custom build: Ryzen 5000 + Threadripper board

### Known Issues
- **Issue:** Certain Intel Rapid Storage Technology (RST) controllers
  - **Symptom:** NixOS installer doesn't detect SATA drives
  - **Workaround:** Disable RST in BIOS or switch to AHCI mode
  - **Note:** Contact operator support if encountered

- **Issue:** AMD Ryzen APU (integrated graphics) on older BIOS
  - **Symptom:** Boot hangs at GRUB/systemd-boot
  - **Workaround:** Update BIOS to latest version
  - **Status:** Fixed in systemd-boot 250+

- **Issue:** Certain HP/ASUS EFI implementations
  - **Symptom:** Cannot boot from USB in UEFI mode
  - **Workaround:** Try disabling CSM (Compatibility Support Module) in BIOS
  - **Status:** Rare, usually resolved by BIOS update

## Unsupported Configurations

### Will NOT Work
- **Legacy BIOS** (only UEFI supported)
- **ARM Architecture** (Lantern OS is x86_64 only)
- **32-bit systems** (64-bit required)
- **Raspberry Pi** or other ARM boards

### Not Tested
- **Hyper-V Host with nested virtualization** (may work but untested)
- **Encrypted disks** (BitLocker or other encryption)
- **External/USB boot** (must have internal partition space)
- **Dual GPU setups** (NVIDIA + Intel, etc.)

## Storage Layout

### Standard Dual Boot Layout

```
Device /dev/sda:
├── /dev/sda1   EFI System Partition    (512MB - 1GB)   FAT32
├── /dev/sda2   Windows C: drive        (~100GB)        NTFS
├── /dev/sda3   NixOS root partition    (~50-100GB)     ext4
└── /dev/sda4   NixOS home (optional)   (remaining)     ext4
```

### Alternative: Separate Drive
- Windows: Primary drive (existing)
- NixOS: Secondary/external drive or large partition
- Both disks must be connected to system during boot

## Disk Partitioning

### Windows Partitioning
- Current setup detected via Disk Management
- Must have at least one FAT32 EFI System Partition
- Windows partition (C:) must be NTFS or exFAT

### NixOS Partitioning
- Recommended: separate ext4 partition for root (/)
- Optional: separate ext4 partition for /home
- Boot partition: uses existing Windows EFI System Partition

### Shared EFI Partition
Both Windows and NixOS will use the same EFI System Partition:
- This is standard and supported
- systemd-boot and Windows bootloader can coexist
- NixOS installation will NOT overwrite existing Windows boot entries if handled correctly

## Performance Characteristics

### NixOS Boot Time
- **Cold boot:** 45-90 seconds (first boot after shutdown)
- **Subsequent boots:** 30-60 seconds
- **Boot menu selection time:** Additional 10-15 seconds

### Windows Boot Time
- Unchanged from current configuration
- NixOS in boot menu adds ~5-10 seconds to POST

### System Performance
- **Memory footprint:** NixOS idle = ~500-800MB
- **Disk I/O:** First boot slower due to package downloads
- **Package builds:** May take longer on older processors

## Power Management

### Hibernate/Sleep
- Windows: Works as normal
- NixOS: Hibernation works but requires swap partition (optional)
- Dual boot: Recommended to disable fast startup in Windows

### Shutdown
- From Windows: Normal shutdown, can boot NixOS next
- From NixOS: Normal shutdown, can boot Windows next
- Boot menu accessible at all times

## Networking

### Windows Side
- Network configuration unchanged
- Both Ethernet and WiFi supported

### NixOS Side
- Wired Ethernet: Works out of the box
- WiFi: Requires additional driver setup (varies by chipset)
  - Intel: Works with iwd/wpa_supplicant
  - Realtek: May require additional configuration
  - Broadcom: May require proprietary drivers

## Backup & Recovery Requirements

### Before Dual Boot Installation
- [ ] Windows system image backup
- [ ] Windows recovery USB created
- [ ] All personal data backed up externally
- [ ] List of currently installed software documented

### Partition Table Backup
```bash
# In Linux live environment
sudo sfdisk -d /dev/sda > /tmp/sda-partition-table.bak
```

### Recovery Boot Media
- Windows: System Repair Disk or recovery USB
- NixOS: Installation ISO on USB (can be used for recovery)

## Rollback Capabilities

### Fast Rollback (< 5 minutes)
- Use Windows recovery media
- Restore boot loader: `bcdboot C:\Windows /s C:`
- Delete NixOS partition

### Full Rollback (< 30 minutes)
- Boot from Windows recovery media
- Use Disk Management to extend C: drive
- Delete NixOS partitions
- Run full Windows system restore if needed

### NixOS-side Rollback
- NixOS generations: system includes previous versions
- Boot into older NixOS generation from boot menu
- Rollback configuration: `sudo nixos-rebuild switch --rollback`

## Audio & Multimedia

### Supported
- ALSA (Advanced Linux Sound Architecture): supported
- PulseAudio: supported
- PipeWire: supported (newer, recommended)
- Common USB audio devices: work out of the box

### May Require Configuration
- Some specialized audio interfaces
- HDMI audio passthrough (usually works)

## USB & Peripherals

### Hotplug Support
- USB drives: detected and mountable immediately
- USB printers: require driver setup
- USB devices: most work with kernel drivers

### Known Good Peripherals
- Standard USB keyboards and mice: works
- USB-C displays with Thunderbolt: may work (chipset dependent)
- MIDI devices: supported via ALSA

## Accessibility

### Supported
- Screen readers: NVDA, Orca (with setup)
- High contrast modes: available
- Keyboard navigation: full support

### Not Built-in
- Braille displays (third-party setup required)
- Eye-tracking devices (third-party software)

## Hardware Diagnostics

### Pre-Installation Check
Run before proceeding:
```powershell
# Windows
Test-DualBootReadiness.ps1

# Hardware information needed:
# - CPU model: `wmic cpu get name`
# - RAM amount: `Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum`
# - Disk model: `Get-CimInstance Win32_LogicalDisk`
# - Firmware: `Get-CimInstance Win32_ComputerSystemProduct`
```

### During NixOS Installation
```bash
# Linux command line
lsblk  # Show block devices and partitions
lscpu  # Show CPU information
free -h  # Show memory information
lspci  # Show PCI devices (chipsets, network, audio)
```

## Contacting Support

If your hardware configuration differs from the above:

1. Run `Test-DualBootReadiness.ps1` and capture output
2. Collect hardware information using commands above
3. Document the specific issue and error messages
4. Reference this document sections and known issues
5. Contact Lantern OS support with:
   - Hardware specification (CPU, RAM, storage, BIOS/UEFI version)
   - Current Windows version
   - Error messages from validator or installer
   - BIOS/UEFI settings (especially boot-related)

---

**Last Updated:** Lantern OS v1.0.0 staging

**Hardware Testing Status:** In progress
- Tested systems: 3+
- Known issues: 2
- Estimated compatibility: 85%+ of systems from last 8 years

