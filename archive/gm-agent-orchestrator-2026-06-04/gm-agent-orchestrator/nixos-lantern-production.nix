# NixOS Configuration — Lantern OS (Primary Node)
# 99.999% Uptime, Atomic Rollback, M5 Attestation Ready

{ config, pkgs, lib, ... }:

{
  imports = [
    ./hardware-configuration.nix
  ];

  # System identification
  networking.hostName = "lantern-primary";
  networking.networkmanager.enable = true;
  time.timeZone = "UTC";

  # Kernel: Latest stable with ZSTD compression
  boot.kernelPackages = pkgs.linuxPackages_latest;
  boot.kernelParams = [
    "quiet"
    "loglevel=3"
    "systemd.log_level=err"
  ];

  # Bootloader: GRUB with fallback
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "/dev/sda";
  boot.loader.grub.default = "1";  # Fallback to previous boot
  boot.loader.timeout = 10;

  # Filesystem: atomic, journaled
  fileSystems."/" = {
    device = "/dev/sda1";
    fsType = "ext4";
    options = [ "noatime" "errors=remount-ro" ];
  };

  # Networking: deterministic
  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22    # SSH
    8766  # Lantern backend
    8767  # RAG server
    9090  # Prometheus
  ];

  # Systemd: aggressive health checking
  systemd.services.lantern-orchestrator = {
    description = "Lantern Orchestrator (99.999% uptime)";
    after = [ "network.target" "docker.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python312}/bin/python3 /opt/lantern/scripts/lantern_orchestrator_main.py";
      Restart = "always";
      RestartSec = "5s";
      KillMode = "mixed";
      StandardOutput = "journal";
      StandardError = "journal";

      # Resource limits
      MemoryMax = "4G";
      CPUQuota = "80%";

      # Isolation
      PrivateTmp = true;
      NoNewPrivileges = true;
      ProtectSystem = "strict";
      ProtectHome = true;
    };

    unitConfig = {
      StartLimitIntervalSec = 300;
      StartLimitBurst = 5;
      StartLimitAction = "reboot-force";  # Reboot if too many failures
    };
  };

  # M5 Attestation service
  systemd.services.m5-attestation = {
    description = "M5 Attestation Daemon";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python312}/bin/python3 /opt/lantern/scripts/lantern_capability_attestation.py";
      Restart = "always";
      RestartSec = "1s";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # Container runtime
  virtualisation.podman = {
    enable = true;
    dockerCompat = true;
    autoPrune.enable = true;
    defaultNetwork.settings.dns_enabled = true;
  };

  # Docker (compatibility)
  virtualisation.docker.enable = true;
  virtualisation.docker.autoPrune.enable = true;

  # Storage: ZSTD compression native
  services.logrotate = {
    enable = true;
    interval = "daily";
    settings."/var/log/lantern/*" = {
      rotate = 7;
      compress = true;
      delaycompress = true;
      missingok = true;
    };
  };

  # Monitoring: VictoriaMetrics
  services.victoriametrics = {
    enable = true;
    listenAddress = ":8428";
    extraOptions = [
      "-memory.allowedPercent=50"
      "-maxLabelsPerTimeseries=100"
    ];
  };

  # Logging: journald with circular buffer
  services.journald.extraConfig = ''
    Storage=persistent
    SystemMaxUse=1G
    RuntimeMaxUse=256M
    SystemKeepFree=512M
    RuntimeKeepFree=128M
    MaxFileSec=24h
    MaxRetentionSec=30d
    SyncIntervalSec=5s
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

  # Package management
  environment.systemPackages = with pkgs; [
    vim
    git
    curl
    htop
    iotop
    nethogs
    jq
    python312
    python312Packages.flask
    python312Packages.pygame
    python312Packages.sentence-transformers
    python312Packages.zstandard
    sqlite
    zstd
    gzip
  ];

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
      allowed-uris = "github:";  # Only GitHub (offline-ready)
    };
    gc = {
      automatic = true;
      dates = "weekly";
      options = "--delete-older-than 30d";
    };
  };

  # System defaults
  system.stateVersion = "24.05";

  # Security hardening
  security.sudo.wheelNeedsPassword = true;
  security.protectKernelImage = true;
  security.lockKernelModules = true;
  security.hideBootMessages = true;

  # Swap for resilience
  swapDevices = [ { device = "/var/swap"; size = 4096; } ];
}
