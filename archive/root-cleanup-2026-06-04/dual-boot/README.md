# Lantern OS Dual Boot Bundle

**Status:** Planning Phase - Ready for Operator Review

This directory contains the complete Lantern OS dual boot setup for Windows/NixOS systems.

## What This Contains

### Core Documents
- **INSTALL-CHECKLIST.md** - Step-by-step installation guide (start here)
- **HARDWARE-ASSUMPTIONS.md** - System requirements and compatibility
- **ROLLBACK-GUIDE.md** - How to revert if needed

### Validation & Setup Scripts
- **Test-DualBootReadiness.ps1** - Pre-flight validation (Windows)
- **NixOS-Config-Stubs/** - References to actual configs in source repos

### Source Repository Links
The actual NixOS configurations live in the orchestrator repo:
```
C:\Users\alexp\Documents\gm-agent-orchestrator\
├── nixos-lantern-production.nix          (base config)
└── nixos-lantern-production-optimized.nix (optimized variant)
```

## Quick Start

### Step 1: Verify Readiness
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Test-DualBootReadiness.ps1
```

Expected: All ✓ checks pass, ⚠ warnings noted.

### Step 2: Review Documentation
1. Read INSTALL-CHECKLIST.md completely
2. Verify HARDWARE-ASSUMPTIONS.md matches your system
3. Review ROLLBACK-GUIDE.md emergency procedures

### Step 3: Prepare Hardware
1. Create full system backup
2. Download NixOS 23.11 LTS from https://nixos.org
3. Create bootable USB with NixOS ISO
4. Gather materials: blank USB, recovery disk

### Step 4: Follow Installation
1. Follow INSTALL-CHECKLIST.md step-by-step
2. All destructive operations require physical action
3. Save installation logs to `manifests/validation/`
4. Post-installation, run convergence loop

## Boundary Rules

**This dual boot system respects these hard boundaries:**

### ✅ What We Do
- Create step-by-step checklists
- Run validation checks
- Guide operator through manual steps
- Document hardware assumptions
- Provide rollback procedures

### ❌ What We NEVER Do
- Automatically resize Windows partitions
- Modify Windows BCD/UEFI without approval
- Install NixOS unattended
- Change firmware boot order automatically
- Mutate bootloader configuration without verification

**All destructive operations require physical operator presence.**

## System Architecture

### Windows Side
- Remains unchanged
- Boots via Windows bootloader
- EFI partition shared with NixOS

### NixOS Side  
- Independent ext4 partition
- systemd-boot bootloader
- Windows boot entry registered
- Can mount and read Windows NTFS partition

### Shared Resources
- EFI System Partition (boot)
- Network configuration
- Hardware resources

## NixOS Configuration Strategy

The NixOS configs are **not copied into this repo** but **referenced from the source**:

### Reason for References Only
1. **Source of truth:** Configs live in orchestrator repo
2. **Mutation safety:** No unattended edits to configs
3. **Transparency:** All changes tracked in source repo
4. **Auditability:** Can see exactly what was run

### To Use the Configs

During NixOS installation, you will:

1. Boot from NixOS USB in live environment
2. Partition your disk as per checklist
3. Mount partitions to `/mnt`
4. Copy the chosen config to `/mnt/etc/nixos/configuration.nix`
5. Run `nixos-install --root /mnt`

**Example during NixOS installation:**
```bash
# From mounted filesystem
cp /mnt/dual-boot/nixos-lantern-production-optimized.nix \
   /mnt/etc/nixos/configuration.nix

# OR

cp /mnt/dual-boot/nixos-lantern-production.nix \
   /mnt/etc/nixos/configuration.nix
```

The configs are staged here for easy access during installation.

## Validation Checklist

Before declaring dual boot ready:

- [ ] All documents review and operator-approved
- [ ] Hardware validation passes
- [ ] NixOS configs copied to staging area
- [ ] Operator confirms backup exists
- [ ] USB media prepared with NixOS ISO
- [ ] BIOS/UEFI access verified
- [ ] No open blocker issues in manifests/open-issues.md

## Known Held Issues

| Issue | Status | Reason |
|-------|--------|--------|
| LANTERN-OS-BOOT-001 | Held | Requires physical operator action and disk mutation |

See manifests/open-issues.md for full list.

## Promotion Criteria

This dual boot bundle is promoted to v1.0.0 when:

1. ✅ All documentation is complete and reviewed
2. ✅ All validation scripts pass on target hardware
3. ✅ At least one successful installation is logged
4. ✅ Post-installation convergence loop validation passes
5. ✅ Operator explicitly approves promotion
6. ✅ Installation logs saved to manifests/validation/

Current status: **Candidate - Ready for Operator Review**

## Next Steps

1. **Operator Review:**
   - Read all documents
   - Verify system matches HARDWARE-ASSUMPTIONS.md
   - Ask questions or flag concerns

2. **Preparation:**
   - Create system backup
   - Download NixOS 23.11 LTS
   - Create bootable USB
   - Clear ~2 hours for installation

3. **Installation:**
   - Follow INSTALL-CHECKLIST.md exactly
   - Document any deviations
   - Save logs and screenshots
   - Test both Windows and NixOS boot

4. **Validation:**
   - Run convergence loop after install
   - Update manifests/validation logs
   - Report success/failure to Lantern OS

5. **Promotion:**
   - If successful, approve promotion to v1.0.0
   - If issues, file them in manifests/open-issues.md
   - Iterate if needed

## Support

For issues or questions:

1. Check ROLLBACK-GUIDE.md for recovery procedures
2. Review HARDWARE-ASSUMPTIONS.md for compatibility
3. Examine INSTALL-CHECKLIST.md troubleshooting section
4. Run Test-DualBootReadiness.ps1 again
5. Save diagnostic output for support

---

**Lantern OS Dual Boot Bundle v1.0.0-rc1**

Ready for operator action and physical installation.

