# Lantern OS Dual Boot Installation Checklist

**Status: PLANNING ONLY - Operator Physical Action Required**

This document guides the operator through setting up a Windows/NixOS dual boot system for Lantern OS v1.0.0.

## ⚠️ CRITICAL BOUNDARIES

**This repository and scripts will NEVER:**
- Resize, partition, or format disks unattended
- Modify Windows BCD (Boot Configuration Data) automatically
- Change firmware/UEFI boot order without explicit operator action
- Install NixOS unattended
- Modify bootloader configuration without operator verification

**All destructive operations require physical operator presence and explicit approval.**

## Pre-Flight Checklist

### Hardware Assumptions

Verify your system meets these requirements:

- [ ] System is UEFI-based (check BIOS/UEFI settings)
- [ ] Secure Boot is disabled or can be disabled
- [ ] Current Windows installation is on NTFS or exFAT
- [ ] At least 50GB free space for NixOS partition
- [ ] System has a spare internal drive OR significant free space on primary drive
- [ ] You have physical access to the computer and boot into BIOS/UEFI

### Backup & Rollback Preparation

- [ ] Full system backup created (e.g., Windows system image)
- [ ] Recovery media created (Windows USB recovery disk)
- [ ] Important data backed up to external drive
- [ ] Windows BitLocker disabled (if enabled)
- [ ] System restore point created

## Step 0: Pre-Installation Validation

Run the validation script to confirm readiness:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\dual-boot\Test-DualBootReadiness.ps1
```

Expected output: All checks pass with no hardware conflicts.

## Step 1: Prepare Windows Side

**Operator Action Required**

1. Boot into Windows
2. Open Disk Management (diskmgmt.msc)
3. Review current disk layout and note:
   - Current C: drive size
   - Total free space
   - Partition structure
4. **Do not resize yet** - we will do this in Step 2 with explicit approval

## Step 2: Resize Windows Partition

**Operator Action Required - Irreversible Step**

Using Windows Disk Management:

1. Right-click C: drive → Shrink Volume
2. Enter shrink size: minimum 50GB (preferably 100GB)
3. Confirm shrink operation
4. **This is destructive. Verify backup before proceeding.**

Expected result: New unallocated space appears on disk

## Step 3: Create NixOS Partition

**Operator Action Required**

Using Windows Disk Management:

1. Right-click unallocated space → New Simple Volume
2. Allocate minimum 50GB for NixOS (/nix and root)
3. Format as ext4 (using Linux tool) OR leave unformatted for NixOS installer
4. Do not assign a drive letter yet
5. Note the partition number or location

## Step 4: Download and Create NixOS Installation Media

**Operator Action - Download & Boot**

1. Download NixOS ISO from https://nixos.org/download.html
   - For Lantern: use 23.11 LTS or later
   - Standard x86_64 architecture

2. Create bootable USB:
   - Windows: Use Rufus, Etcher, or similar
   - Insert USB drive
   - Select NixOS ISO
   - Write to USB (this will erase the USB)

3. Reboot computer with USB inserted

## Step 5: Boot NixOS Installer

**Operator Action - Physical Boot**

1. Reboot with NixOS USB inserted
2. Enter BIOS/UEFI setup (press F2, F12, DEL, or ESC during POST - check your system)
3. Change boot order to boot from USB
4. Save and exit
5. System should boot into NixOS installer

## Step 6: Partition and Format in NixOS

**Operator Action in NixOS Live Environment**

```bash
# Identify your disk and partitions
lsblk

# Example: if /dev/sda is your primary disk and you created a partition:
# /dev/sda1 = Windows (existing)
# /dev/sda2 = NixOS partition (unallocated or unformatted)

# Format the NixOS partition (DANGEROUS - make sure this is the right partition!)
mkfs.ext4 /dev/sda2

# Create mount point
mkdir -p /mnt

# Mount the partition
mount /dev/sda2 /mnt

# Create boot subdirectory for ESP (EFI System Partition) mount
mkdir -p /mnt/boot

# Mount Windows EFI partition (usually /dev/sda1)
# Note: Find the EFI partition with: lsblk -n -o NAME,TYPE,FSTYPE | grep vfat
# It's usually /dev/sda1 in a dual-boot setup
mount /dev/sda1 /mnt/boot
```

## Step 7: Copy Lantern NixOS Configuration

**From Lantern OS Repository**

Copy the appropriate configuration:

```bash
# Option A: Optimized production config
cp /mnt/dual-boot/nixos-lantern-production-optimized.nix /mnt/etc/nixos/configuration.nix

# Option B: Base production config
cp /mnt/dual-boot/nixos-lantern-production.nix /mnt/etc/nixos/configuration.nix
```

Review the config before installation:

```bash
cat /mnt/etc/nixos/configuration.nix
```

**Verify these critical settings:**
- [ ] Boot loader is set to systemd-boot (NOT GRUB)
- [ ] EFI partition is /mnt/boot
- [ ] Root filesystem is /dev/sda2 (or your NixOS partition)
- [ ] Windows is listed in boot loader entries
- [ ] No unattended actions in the config

## Step 8: Run NixOS Installer

**In NixOS Live Environment**

```bash
# Generate hardware configuration
nixos-generate-config --root /mnt

# Run the installer
nixos-install --root /mnt
```

This will:
- Download and build NixOS
- Install to /mnt
- Create systemd-boot entries
- Do NOT reboot automatically (you must do this)

Expected time: 15-45 minutes depending on system and network

## Step 9: Manual Bootloader Configuration

**Operator Action - Bootloader Setup**

After NixOS installation completes, you must manually configure the bootloader entry for Windows:

```bash
# Mount the EFI partition if not already mounted
mount /dev/sda1 /mnt/boot

# Create a boot entry for Windows
# (systemd-boot configuration - check the generated entries)
ls /mnt/boot/loader/entries/

# Create Windows entry if needed:
cat > /mnt/boot/loader/entries/windows.conf <<EOF
title Windows
efi /EFI/Microsoft/Boot/bootmgfw.efi
EOF
```

## Step 10: Reboot and Test

**Operator Action**

1. Remove NixOS USB
2. Reboot system
3. Watch boot menu - should show:
   - NixOS (systemd-boot default)
   - Windows (manual entry)
4. Test Windows boot: select "Windows" from boot menu
5. Verify Windows still boots and functions correctly
6. Boot back into NixOS

## Rollback: Return to Windows-Only

If the installation fails or you want to revert:

1. Boot from Windows recovery media
2. Use Startup Repair or Recovery Environment
3. Run: `bcdboot C:\Windows /s C:`
4. Delete the NixOS partition using Disk Management
5. Extend Windows partition back to original size

## Post-Installation: Register with Lantern OS

After successful dual boot:

1. Boot into NixOS
2. Verify all Lantern OS services are running
3. Create a validation report:

```bash
# In NixOS
sudo systemctl status lantern-*
uname -a
nixos-version
```

4. Update `manifests/dual-boot.md` with:
   - Actual hardware used
   - NixOS version installed
   - Validation results
   - Any custom config changes
   - Operator approval timestamp

## Known Issues & Troubleshooting

### Issue: No boot menu appears

**Solution:**
- Enter BIOS/UEFI setup
- Confirm USB is in boot priority list
- Disable Secure Boot if still enabled
- Try different USB port

### Issue: NixOS boots but Windows doesn't appear

**Solution:**
- Reboot into NixOS
- Run `systemctl reboot --firmware-setup`
- Check UEFI boot order
- Ensure EFI partition is mounted at /boot
- Verify Windows boot entry exists: `efibootmgr`

### Issue: Windows boots but NixOS doesn't appear

**Solution:**
- Boot into Windows
- Run `bcdboot C:\Windows /s C:` to restore Windows boot order
- Boot NixOS from USB
- Reinstall boot loader: `nixos-install --root /mnt`

### Issue: Cannot shrink Windows partition

**Solution:**
- Disable hibernation: `powercfg /hibernate off`
- Disable virtual memory: System Properties → Advanced → Virtual Memory
- Run defragmentation before shrinking
- Try from Safe Mode with Command Prompt

## Support & Evidence

- Installation log: saved to `/var/log/lantern-install.log`
- Hardware report: saved to `/var/log/hardware-info.txt`
- Before/after disk screenshots recommended

---

**Next: Run convergence loop validation**

After successful installation, run the convergence loop to validate:

```powershell
cd C:\tmp\lantern-os
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
```

