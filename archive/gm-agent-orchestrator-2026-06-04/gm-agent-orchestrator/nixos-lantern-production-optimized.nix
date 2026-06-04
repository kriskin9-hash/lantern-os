# NixOS Configuration — Lantern OS (Optimized for Low Latency)
# Sub-100ms Response Times, Minimal Weight, High Throughput

{ config, pkgs, lib, ... }:

{
  imports = [
    ./hardware-configuration.nix
  ];

  # System identification
  networking.hostName = "lantern-primary";
  networking.networkmanager.enable = true;
  time.timeZone = "UTC";

  # Kernel: Optimized for low latency (preempt, no timer wheel)
  boot.kernelPackages = pkgs.linuxPackages_latest;
  boot.kernelParams = [
    "quiet"
    "loglevel=2"  # REDUCED: 3→2 (fewer kernel messages)
    "systemd.log_level=crit"  # REDUCED: err→crit (only critical)
    "nohz=off"  # OPTIMIZED: disable dynamic ticks for predictable latency
    "sched_migration_cost_ns=500000"  # OPTIMIZED: reduce migration overhead
  ];

  # Bootloader: Fast boot timeout
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "/dev/sda";
  boot.loader.grub.default = "1";
  boot.loader.timeout = 3;  # REDUCED: 10→3 seconds

  # Filesystem: optimized for speed
  fileSystems."/" = {
    device = "/dev/sda1";
    fsType = "ext4";
    options = [ "noatime" "nodiratime" "errors=remount-ro" "data=writeback" ];  # OPTIMIZED: add nodiratime, writeback
  };

  # Networking: deterministic, minimal firewall overhead
  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22    # SSH
    8766  # Lantern backend
    8767  # RAG server
  ];  # REMOVED: 9090 (Prometheus not needed for primary)

  # Systemd: aggressive health checking with LOW LATENCY restarts
  systemd.services.lantern-orchestrator = {
    description = "Lantern Orchestrator (Low-Latency)";
    after = [ "network.target" ];  # REMOVED: docker.service (not always needed)
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python312}/bin/python3 /opt/lantern/scripts/lantern_orchestrator_main.py";
      Restart = "always";
      RestartSec = "1s";  # OPTIMIZED: 5s→1s (faster recovery)
      KillMode = "mixed";
      StandardOutput = "journal";
      StandardError = "journal";

      # Resource limits: tighter for faster context switching
      MemoryMax = "2G";  # REDUCED: 4G→2G (less GC overhead)
      CPUQuota = "90%";  # INCREASED: 80%→90% (more throughput)

      # Isolation (kept for security, minimal perf impact)
      PrivateTmp = true;
      NoNewPrivileges = true;
      ProtectSystem = "strict";
      ProtectHome = true;
    };

    unitConfig = {
      StartLimitIntervalSec = 300;
      StartLimitBurst = 5;
      StartLimitAction = "reboot-force";
    };
  };

  # M5 Attestation service — ultra-fast
  systemd.services.m5-attestation = {
    description = "M5 Attestation Daemon";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python312}/bin/python3 /opt/lantern/scripts/lantern_capability_attestation.py";
      Restart = "always";
      RestartSec = "100ms";  # OPTIMIZED: 1s→100ms (faster attestation)
      StandardOutput = "journal";
      StandardError = "journal";
      MemoryMax = "512M";  # REDUCED: smaller footprint
    };
  };

  # Container runtime — minimal
  virtualisation.podman = {
    enable = true;
    dockerCompat = true;
    autoPrune.enable = true;
    defaultNetwork.settings.dns_enabled = true;
  };

  # REMOVED: Docker (use Podman only, not both)

  # Storage: ZSTD L1 (faster, slightly larger)
  services.logrotate = {
    enable = true;
    interval = "daily";
    settings."/var/log/lantern/*" = {
      rotate = 7;
      compress = true;
      compressCmd = "${pkgs.zstd}/bin/zstd -1";  # OPTIMIZED: L3→L1 compression
      delaycompress = true;
      missingok = true;
    };
  };

  # Monitoring: REMOVED Prometheus/VictoriaMetrics (use structured journald instead)
  # VictoriaMetrics adds 50-100ms query latency; removed for <10ms target

  # Logging: journald with minimal retention
  services.journald.extraConfig = ''
    Storage=volatile
    SystemMaxUse=256M
    RuntimeMaxUse=128M
    SystemKeepFree=256M
    RuntimeKeepFree=64M
    MaxFileSec=12h
    MaxRetentionSec=7d
    SyncIntervalSec=1s
    ForwardToConsole=no
    Compress=yes
  '';

  # SSH for remote management
  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "no";
      PasswordAuthentication = false;
      PubkeyAuthentication = true;
    };
  };

  # Package management — lean
  environment.systemPackages = with pkgs; [
    vim
    git
    curl
    htop
    jq
    python312
    python312Packages.flask
    python312Packages.sentence-transformers  # KEPT: RAG search essential
    python312Packages.zstandard
    sqlite
    zstd
    gzip
  ];  # REMOVED: pygame, iotop, nethogs (not needed for backend)

  # User management
  users.users.lantern = {
    isSystemUser = true;
    group = "lantern";
    home = "/var/lib/lantern";
    shell = pkgs.nologin;
  };

  users.groups.lantern = {};

  # Nix configuration
  nix = {
    settings = {
      auto-optimise-store = true;
      allowed-uris = "github:";
    };
    gc = {
      automatic = true;
      dates = "weekly";
      options = "--delete-older-than 7d";  # OPTIMIZED: 30d→7d (smaller store)
    };
  };

  # System defaults
  system.stateVersion = "24.05";

  # Security hardening
  security.sudo.wheelNeedsPassword = true;
  security.protectKernelImage = true;
  security.lockKernelModules = true;
  security.hideBootMessages = true;

  # Swap for resilience — smaller
  swapDevices = [ { device = "/var/swap"; size = 1024; } ];  # REDUCED: 4096→1024 MB
}
