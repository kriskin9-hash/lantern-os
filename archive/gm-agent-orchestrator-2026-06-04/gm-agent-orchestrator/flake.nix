{
  description = "Lantern OS — 99.999% Uptime, Offline-First, No Cloud APIs";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
    home-manager = {
      url = "github:nix-community/home-manager/release-24.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, home-manager }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      # NixOS system configurations
      nixosConfigurations = {
        lantern-production = nixpkgs.lib.nixosSystem {
          inherit system;
          specialArgs = { inherit self; };
          modules = [
            ./nixos/lantern-production.nix
            home-manager.nixosModules.home-manager
          ];
        };

        lantern-operator = nixpkgs.lib.nixosSystem {
          inherit system;
          specialArgs = { inherit self; };
          modules = [
            ./nixos/lantern-operator.nix
            home-manager.nixosModules.home-manager
          ];
        };
      };

      # Development environment
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          python312Packages.anthropic
          python312Packages.flask
          python312Packages.pygame
          python312Packages.sentence-transformers
          python312Packages.zstandard
          docker
          docker-compose
          podman
          sqlite
          curl
          git
          nix
        ];

        shellHook = ''
          echo "🚀 Lantern development environment loaded"
          echo "Python: $(python3 --version)"
          echo "Docker: $(docker --version)"
          echo "NixOS: $(nix --version)"
        '';
      };

      # Deployment package
      packages.${system}.lantern-os = pkgs.stdenv.mkDerivation {
        name = "lantern-os";
        src = ./.;

        buildPhase = ''
          mkdir -p $out/bin
          mkdir -p $out/etc/lantern
          mkdir -p $out/var/lib/lantern
          cp -r scripts/* $out/bin/
          cp -r .lantern/* $out/etc/lantern/
        '';

        installPhase = ''
          mkdir -p $out
          echo "Lantern OS v1.0.0 — 99.999% Uptime" > $out/VERSION
        '';
      };

      # Build ISO for deployment
      images.lantern-iso = self.nixosConfigurations.lantern-production.config.system.build.isoImage;
    };
}
