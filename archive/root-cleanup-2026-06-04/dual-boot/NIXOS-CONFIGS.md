# NixOS Configurations for Lantern OS Dual Boot

This document explains how NixOS configurations are used in the dual boot setup.

## Configuration Strategy

The actual NixOS configuration files are **not copied into this repository** but **sourced from the orchestrator repository**. This ensures:

1. **Single source of truth** - configs live in their canonical location
2. **Change tracking** - all modifications visible in orchestrator repo
3. **Mutation safety** - no unattended config changes
4. **Auditability** - full history of what was run

## Source Repositories

### Primary Source
```
C:\Users\alexp\Documents\gm-agent-orchestrator\
├── nixos-lantern-production.nix          (Base configuration)
└── nixos-lantern-production-optimized.nix (Optimized variant)
```

### Alternative Source (if in NixOS live environment)
```
/mnt/dual-boot/
├── nixos-lantern-production.nix
└── nixos-lantern-production-optimized.nix
```

## Available Configurations

### 1. Base Production (`nixos-lantern-production.nix`)

**Recommended for:** First-time installations, standard hardware

**Features:**
- Core Lantern OS services
- Standard NixOS packages
- Stable configuration
- Moderate boot time
- Good compatibility

**Usage:**
```bash
# During NixOS installation
cp /mnt/dual-boot/nixos-lantern-production.nix \
   /mnt/etc/nixos/configuration.nix

# Then run installer
nixos-install --root /mnt
```

**Size:** ~1.5-2GB after first build

### 2. Optimized Production (`nixos-lantern-production-optimized.nix`)

**Recommended for:** Systems with fast SSDs, smaller partitions, performance-focused

**Features:**
- All features from base configuration
- Additional optimizations
- Reduced disk footprint
- Faster startup
- More aggressive caching

**Usage:**
```bash
# During NixOS installation
cp /mnt/dual-boot/nixos-lantern-production-optimized.nix \
   /mnt/etc/nixos/configuration.nix

# Then run installer
nixos-install --root /mnt
```

**Size:** ~1-1.5GB after first build

## Configuration Locations During Installation

### In Windows (Before Boot)
```
C:\Users\alexp\Documents\gm-agent-orchestrator\
```

Copy one file to USB before rebooting into NixOS.

### During NixOS Installation (Live Environment)
```
/mnt/dual-boot/
```

Files are accessible at this path after mounting the NixOS partition.

### Post-Installation (Final Location)
```
/etc/nixos/configuration.nix
```

Your chosen configuration becomes the active system config.

## Configuration Usage During Install

### Step-by-Step

1. **Boot NixOS live environment** from USB

2. **Partition your disk** (follow INSTALL-CHECKLIST.md)

3. **Mount filesystems:**
   ```bash
   mount /dev/sda3 /mnt           # Root partition
   mount /dev/sda1 /mnt/boot      # EFI partition
   ```

4. **Copy configuration:**
   ```bash
   # Choose either base or optimized:
   
   # Option A: Base (most compatible)
   cp /mnt/dual-boot/nixos-lantern-production.nix \
      /mnt/etc/nixos/configuration.nix
   
   # OR Option B: Optimized (performance)
   cp /mnt/dual-boot/nixos-lantern-production-optimized.nix \
      /mnt/etc/nixos/configuration.nix
   ```

5. **Review before installing:**
   ```bash
   cat /mnt/etc/nixos/configuration.nix
   ```
   
   **Verify these settings:**
   - [ ] Boot loader is systemd-boot (NOT GRUB)
   - [ ] Root filesystem matches your partition
   - [ ] Hostname is set correctly
   - [ ] System description is accurate
   - [ ] No hardcoded paths for your specific setup

6. **Run installer:**
   ```bash
   nixos-install --root /mnt
   ```

7. **After installation completes, reboot:**
   ```bash
   reboot
   ```

## Customization After Installation

### Modify Configuration Post-Install

Once NixOS is installed, you can modify the configuration:

```bash
# Boot into NixOS
# Edit the configuration
sudo nano /etc/nixos/configuration.nix

# Apply changes
sudo nixos-rebuild switch

# Or test without applying (doesn't affect current system)
sudo nixos-rebuild test

# Roll back if needed
sudo nixos-rebuild switch --rollback
```

### Version Control Configuration

Track your customizations:

```bash
# Initialize git in /etc/nixos
cd /etc/nixos
sudo git init
sudo git add configuration.nix hardware-configuration.nix
sudo git commit -m "Initial configuration"

# After changes
sudo git diff
sudo git add .
sudo git commit -m "Description of changes"
```

## Hardware-Specific Customization

### Generated Hardware Configuration

During installation, NixOS generates hardware-specific settings:

```bash
/mnt/etc/nixos/hardware-configuration.nix  # Generated automatically
```

**Do not modify manually unless you know what you're doing.**

This file contains:
- Filesystem UUIDs and mount points
- Bootloader settings
- Module requirements for your hardware
- CPU microcode updates (Intel/AMD)
- Available kernels for your system

## Validation Commands

### Pre-Install Validation

```bash
# In NixOS live environment
# Check if configuration is syntactically valid
nix-instantiate /mnt/etc/nixos/configuration.nix

# Or if already in the NixOS being installed
sudo nix-instantiate /etc/nixos/configuration.nix
```

### Post-Install Validation

```bash
# Boot into NixOS
# Check current system
uname -a
nixos-version

# List what changed from default
nix-shell -p diffutils <<'EOF'
diff <(cat /etc/nixos/configuration.nix) <(nix show-config)
EOF

# Check systemd services
systemctl status

# Check disk space used
du -sh /nix /var /etc/nixos
```

## Comparing Configurations

### Differences Between Base and Optimized

```bash
# If both files are available
diff nixos-lantern-production.nix \
     nixos-lantern-production-optimized.nix
```

**Common optimizations include:**
- Disabled services not needed
- Reduced closure size
- Aggressive garbage collection settings
- Smaller rebuild times
- Fewer debug symbols

## Rollback Configuration

### If Configuration Breaks Boot

```bash
# Boot into previous generation from boot menu
# Then:
sudo nixos-rebuild switch --rollback

# Or boot directly into previous generation:
# Select from systemd-boot "Previous Configuration"
```

### View Configuration History

```bash
# List all previous system generations
nix-env --list-generations -p /nix/var/nix/profiles/system

# Boot a specific older generation
# Via systemd-boot menu at next reboot
```

## Updating Configurations

### Update NixOS Channel

```bash
# After successfully booting
sudo nix-channel --update

# Rebuild with latest packages
sudo nixos-rebuild switch --upgrade
```

### Safe Update Procedure

```bash
# 1. Test without applying
sudo nixos-rebuild test --upgrade

# 2. If works, apply for real
sudo nixos-rebuild switch --upgrade

# 3. If breaks, rollback
sudo nixos-rebuild switch --rollback
```

## Configuration Features

### Included in Both Configurations

- NixOS 23.11 LTS (or later)
- Systemd boot loader
- Essential system utilities
- Networking stack (NetworkManager or systemd-networkd)
- SSH server (optional, can be disabled)
- User account support
- Sudo permissions for designated users
- Standard shell environments

### Services in Base Configuration

- [ ] Network manager or systemd-networkd
- [ ] DHCP client for automatic network
- [ ] DNS resolver configuration
- [ ] Firewall (if configured)
- [ ] SSH (if enabled)
- [ ] NTP time synchronization

### Additional Services in Optimized

- Aggressive garbage collection
- Reduced log retention
- Faster rebuilds
- Smaller closure size

## Environment Variables in Configuration

### How to Set Variables

```nix
# In /etc/nixos/configuration.nix
environment.sessionVariables = {
  PATH = "/path/to/bin:${config.env.PATH}";
};

environment.systemPackages = with pkgs; [
  # List packages here
];
```

## Secrets Management

### Important Security Note

**Never include secrets in configuration.nix:**
- Passwords
- API keys
- Private keys
- Database credentials

Instead, manage via:
1. **agenix** (recommended for NixOS)
2. **systemd-creds** (systemd native)
3. **External key management** (Vault, etc.)

See orchestrator repo for example secret management.

## Multi-User Setup

### Adding Users to Configuration

```nix
users.users.newuser = {
  isNormalUser = true;
  home = "/home/newuser";
  createHome = true;
  shell = pkgs.bash;
  extraGroups = [ "wheel" ];
};
```

Then apply:
```bash
sudo nixos-rebuild switch
```

## Boot Configuration Details

### Systemd-Boot Entries

Generated during install:
```
/boot/loader/entries/nixos-*.conf
/boot/loader/entries/windows.conf      # (manual, see INSTALL-CHECKLIST)
```

### Bootloader Settings

```
/boot/loader/loader.conf
```

Contains:
- Default boot entry
- Boot timeout
- Console options
- Editor setting

### Do NOT Manually Edit

- `/boot/EFI/` - Use nixos-rebuild to update
- `/boot/loader/` - NixOS manages these

---

## Support & Documentation

### For Configuration Help

1. Check NixOS manual: https://nixos.org/manual/nixos/stable/
2. Review orchestrator repo documentation
3. Check NixOS community wiki: https://nixos.wiki/
4. Search nixos-help or ask in forums

### For Issues with Configuration

1. Save current config backup
2. Review changes with `nixos-rebuild test`
3. Check logs: `journalctl -xe`
4. Roll back if needed: `nixos-rebuild switch --rollback`

---

**Lantern OS NixOS Configuration Guide v1.0.0**

Configuration source repo: `C:\Users\alexp\Documents\gm-agent-orchestrator\`

