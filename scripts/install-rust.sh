#!/usr/bin/env bash
# Install Rust toolchain for Lantern OS contributors (Unix/Linux/macOS).
# Run: bash scripts/install-rust.sh

set -euo pipefail

if command -v rustc &>/dev/null && command -v cargo &>/dev/null; then
    echo "Rust already installed: $(rustc --version) / $(cargo --version)"
    exit 0
fi

echo "Rust not found. Installing via rustup..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile default

# shellcheck source=/dev/null
source "$HOME/.cargo/env"

if ! command -v rustc &>/dev/null; then
    echo "Error: Installation appeared to succeed but rustc is not on PATH. Restart your terminal." >&2
    exit 1
fi

echo "Rust installation complete: $(rustc --version)"

CSF_RUST_DIR="$(cd "$(dirname "$0")/../src/csf_rust" && pwd)"
echo "Quick sanity build in $CSF_RUST_DIR ..."
cd "$CSF_RUST_DIR"
cargo build --release

echo "Done. You can now run 'cargo test' in src/csf_rust/"
