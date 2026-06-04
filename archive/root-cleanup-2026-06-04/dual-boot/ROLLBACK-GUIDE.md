# Dual Boot Rollback Guide

This guide explains how to recover from dual boot installation issues or roll back to Windows-only.

## Quick Reference

| Scenario | Time | Difficulty | Data Risk |
|----------|------|------------|-----------|
| Can't boot NixOS | 5 min | Easy | None |
| Can't boot Windows | 10 min | Medium | None if backup exists |
| Complete rollback | 30 min | Medium | None if backup exists |
| Corrupted Windows | 1+ hour | Hard | High without backup |

## Scenario 1: NixOS Won't Boot

### Symptoms
- Bootloader hangs
- NixOS doesn't appear in boot menu
- systemd-boot error messages

### Recovery Steps

#### Option 1A: Use Boot Menu (Fastest)

1. **Reboot computer**
2. **Enter boot menu** (usually F12, ESC, or DEL during POST - check your system)
3. **Select Windows** boot option
4. **Boot into Windows**

Windows should work normally. NixOS can be debugged later.

#### Option 1B: Boot from NixOS USB (If menu fails)

1. **Insert NixOS USB** into computer
2. **Reboot and enter BIOS/UEFI**
3. **Change boot priority** to USB device first
4. **Save and exit BIOS**
5. **NixOS installer should boot**
6. **Don't run installer** - just use `chroot` to diagnose

```bash
# In NixOS live environment
mount /dev/sda3 /mnt  # Mount NixOS partition
mount /dev/sda1 /mnt/boot  # Mount EFI partition
chroot /mnt  # Enter NixOS environment

# Diagnose issue
journalctl -b -e  # See boot logs
systemctl status  # Check system status
ls /boot/loader/entries/  # Check boot entries

# Exit if needed
exit
```

#### Option 1C: Repair Bootloader (Advanced)

If NixOS boots but can't start services:

```bash
# In chroot as above
nixos-rebuild switch --root /mnt
# or
nixos-install --root /mnt --no-root-passwd
```

### Prevention
- Keep NixOS USB for future recovery
- Save the NixOS installation log
- Don't manually edit `/boot/loader/` after installation

---

## Scenario 2: Windows Won't Boot

### Symptoms
- Windows not in boot menu
- Boot hangs before Windows logo
- "Invalid partition table" errors

### Recovery Steps

#### Option 2A: Restore from Boot Manager

1. **Reboot and enter BIOS/UEFI** (F2, F12, DEL during POST)
2. **Look for "Boot" or "Boot Order" menu**
3. **Check if "Windows Boot Manager" exists**
4. **Move it to top priority** if found
5. **Save and exit BIOS**
6. **Reboot**

#### Option 2B: Rebuild Windows Boot Loader (Requires Windows Recovery USB)

**Requirements:**
- Windows system recovery USB or installation media
- Physical access to boot into Recovery Environment

1. **Insert Windows recovery/installation USB**
2. **Reboot and enter BIOS/UEFI**
3. **Set USB as boot priority**
4. **Boot from USB**
5. **At Windows installer screen, press SHIFT+F10** (opens Command Prompt)
6. **Run these commands:**

```cmd
# Show current disk status
diskpart
list disk

# Select the correct disk (usually disk 0)
select disk 0
list partition

# Exit diskpart
exit

# Rebuild boot loader
bcdboot C:\Windows /s C: /f ALL
```

7. **Reboot** (remove USB)
8. **Windows should boot**

#### Option 2C: Full Windows System Restore

If boot commands don't work:

1. **Use Windows recovery USB**
2. **Click "Repair your computer"**
3. **Choose "Advanced options" → "System Restore"** or **"System Image Recovery"**
4. **Restore to pre-dual-boot backup**
5. **Reboot**

### Prevention
- Keep Windows recovery USB up to date
- Create system image before dual boot
- Don't delete Windows EFI boot files
- Backup `C:\EFI\Microsoft\` folder

---

## Scenario 3: Both Systems Won't Boot

### Cause
Usually: partitioning issue or corrupted EFI partition

### Recovery Steps

#### Step 1: Boot from NixOS USB

1. **Insert NixOS USB**
2. **Reboot, enter BIOS/UEFI, set USB to boot first**
3. **Boot into NixOS live environment**

#### Step 2: Diagnose Partition Table

```bash
# In NixOS live environment
lsblk  # Shows current partition layout
fdisk -l /dev/sda  # Detailed partition info
cat /etc/fstab  # Check mounted filesystems
efibootmgr  # Show EFI boot entries
```

#### Step 3: Fix Partition Table (if corrupted)

```bash
# DANGEROUS - only if you have backup

# Restore from backup (if you created one)
sfdisk /dev/sda < /tmp/sda-partition-table.bak

# OR manually rebuild partitions (advanced - requires caution)
```

#### Step 4: Boot Recovery Media

1. **If NixOS partition is okay:** Skip to "Recover Windows"
2. **If NixOS partition is corrupted:** Proceed to "Recover NixOS"

---

## Scenario 4: Complete Rollback (Remove NixOS, Return to Windows-Only)

### When to Use This
- Dual boot not working after multiple attempts
- Operator wants Windows-only again
- Troubleshooting NixOS issues

### Requirements
- Windows recovery USB or installation media
- Backup of system (if possible)
- ~30 minutes

### Rollback Steps

#### Step 1: Boot Windows Recovery

1. **Insert Windows recovery USB**
2. **Reboot, select USB in boot menu**
3. **Click "Repair your computer"**

#### Step 2: Delete NixOS Partition

1. **Click "Advanced options" → "Command Prompt"**
2. **Run:**

```cmd
# Open disk manager
diskpart

# List disks
list disk

# Select correct disk
select disk 0

# List partitions
list partition

# Select NixOS partition (usually partition 3)
select partition 3

# Delete it
delete partition override

# If you have a separate /home partition, repeat for that too
# Then exit
exit
```

#### Step 3: Extend Windows Partition

1. **In Windows recovery environment**
2. **Right-click on C: drive**
3. **Choose "Extend Volume"**
4. **Select all unallocated space**
5. **Click "Extend"**

OR via command line:

```cmd
diskpart
select disk 0
select partition 2  # C: drive
extend
exit
```

#### Step 4: Repair Windows Boot Loader

```cmd
# In Command Prompt from recovery media
bcdboot C:\Windows /s C: /f ALL
```

#### Step 5: Reboot

1. **Remove USB**
2. **Reboot**
3. **Windows should boot normally**

### Verification
```cmd
# Boot into Windows
# Verify drive size expanded
diskpart
select disk 0
list partition
# C: should now be much larger
exit
```

---

## Scenario 5: Corrupted Windows (NixOS works)

### Situation
- NixOS boots fine
- Windows partition is damaged
- System restore USB available

### Recovery Steps

1. **Boot into NixOS** (using boot menu)
2. **Create backup of Windows partition if possible:**

```bash
# Mount Windows partition (read-only)
sudo mount /dev/sda2 /mnt -o ro
tar -czf /tmp/windows-backup.tar.gz /mnt/*
# Transfer backup to USB if possible
```

3. **Insert Windows recovery USB**
4. **Reboot, boot from USB**
5. **Use "System Restore" or "Repair" options**

6. **If Windows is beyond repair:**
   - Follow Scenario 4 (Complete Rollback)
   - Or reinstall Windows on same partition

---

## Scenario 6: EFI Partition Corrupted

### Symptoms
- Neither OS boots
- No boot menu appears

### Risk Level
**CRITICAL** - EFI partition shared by both systems

### Prevention First
```bash
# Create backup during NixOS installation
cp -r /boot/EFI /backup/EFI-backup
tar -czf /tmp/efi-backup.tar.gz /boot/EFI
```

### Recovery

1. **Boot from NixOS USB**
2. **Mount filesystems:**

```bash
mount /dev/sda3 /mnt
mount /dev/sda1 /mnt/boot
```

3. **If you have a backup:**

```bash
# Restore EFI partition
rm -rf /mnt/boot/EFI
tar -xzf /tmp/efi-backup.tar.gz -C /mnt/boot
```

4. **If no backup, rebuild:**

```bash
# In chroot
chroot /mnt

# Reinstall bootloaders
nixos-install --root /mnt

# Then from Windows recovery USB:
bcdboot C:\Windows /s C: /f ALL
```

---

## Scenario 7: Dual Boot Works But Slow

### Diagnosis

```bash
# In NixOS
# Check boot time
systemd-analyze
systemd-analyze blame

# In Windows
# Check boot time via Event Viewer
wevtutil qe System /c:10 /rd:true /f:text | grep -i "boot time"
```

### Common Fixes

#### NixOS slow
```bash
sudo nixos-rebuild switch --update-input nixpkgs
sudo nix-gc  # Clean up old packages
```

#### Windows slow  
- Disable unnecessary startup programs
- Run Disk Cleanup
- Defragment disk
- Disable hibernation if not using

---

## Emergency Contacts & Logs

### Important Logs to Save

**Windows:**
```cmd
# Event Viewer logs for boot failures
wevtutil qe System /rd:true > boot-log.txt
```

**NixOS:**
```bash
# Boot journal
sudo journalctl -b > nix-boot-log.txt
sudo systemd-analyze > nix-boot-analysis.txt
```

### Before Seeking Help
1. Save all relevant logs
2. Document exact steps taken
3. Note error messages exactly
4. Have hardware info ready (see HARDWARE-ASSUMPTIONS.md)
5. Confirm partition table backup exists

---

## Prevention Checklist

- [ ] Created full Windows system backup
- [ ] Created Windows recovery USB
- [ ] Saved partition table backup to external drive
- [ ] Documented BIOS/UEFI settings before changes
- [ ] Kept NixOS installation ISO on USB
- [ ] Created NixOS boot USB for recovery
- [ ] Saved EFI partition backup
- [ ] Documented current boot entries (`efibootmgr`)
- [ ] Documented Windows boot configuration (`bcdedit /enum`)

---

## Rollback Summary

| Failure | Time to Recover | Data Loss Risk |
|---------|-----------------|----------------|
| NixOS boot | < 5 min | None |
| Windows boot | 10-15 min | None if backup exists |
| Partition corruption | 30+ min | Moderate without backup |
| EFI corruption | 1+ hour | High without backup |
| Complete failure | 2+ hours | Very high without backup |

**Always maintain backups before attempting dual boot.**

---

**Last Updated:** Lantern OS v1.0.0-rc1

For current rollback procedures, see the latest version in `C:\tmp\lantern-os\dual-boot\`

