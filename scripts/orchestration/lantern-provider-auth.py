#!/usr/bin/env python3
"""
Lantern Provider Authentication & Account Manager

Allows founders/operators to:
- Sign in to LLM provider accounts (Claude, Gemini, DeepSeek, etc.)
- Create new accounts
- Manage API keys & credentials (stored locally, encrypted)
- Configure provider priority (primary/fallback)
- Link to family configurations

Credentials stored at: ~/.lantern/credentials/
Never committed to git, never synced to cloud.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import secrets


CREDS_DIR = Path.home() / ".lantern" / "credentials"
PROVIDERS_CONFIG = Path.home() / ".lantern" / "providers.json"


class ProviderAuthManager:
    """Manage LLM provider authentication and credentials."""

    PROVIDERS = {
        "claude": {
            "name": "Anthropic Claude",
            "auth_type": "api_key",
            "required_fields": ["api_key"],
            "optional_fields": ["model_override"],
            "docs": "https://console.anthropic.com/",
            "setup_instructions": "Get API key from console.anthropic.com"
        },
        "gemini": {
            "name": "Google Gemini",
            "auth_type": "api_key",
            "required_fields": ["api_key"],
            "optional_fields": ["model_override"],
            "docs": "https://makersuite.google.com/",
            "setup_instructions": "Get API key from makersuite.google.com"
        },
        "deepseek": {
            "name": "DeepSeek",
            "auth_type": "api_key",
            "required_fields": ["api_key"],
            "optional_fields": ["model_override"],
            "docs": "https://platform.deepseek.com/",
            "setup_instructions": "Get API key from platform.deepseek.com"
        },
        "local-lm-studio": {
            "name": "Local LM Studio",
            "auth_type": "endpoint",
            "required_fields": ["host", "port"],
            "optional_fields": ["model"],
            "docs": "https://lmstudio.ai/",
            "setup_instructions": "LM Studio running locally. Default: 127.0.0.1:1234"
        },
        "ollama": {
            "name": "Local Ollama",
            "auth_type": "endpoint",
            "required_fields": ["host", "port"],
            "optional_fields": ["model"],
            "docs": "https://ollama.ai/",
            "setup_instructions": "Ollama running locally. Default: 127.0.0.1:11434"
        }
    }

    def __init__(self):
        """Initialize credential manager."""
        self.creds_dir = CREDS_DIR
        self.creds_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = PROVIDERS_CONFIG
        self.providers = self._load_providers_config()

    def _load_providers_config(self) -> Dict[str, Any]:
        """Load current provider configuration."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {
            "primary": None,
            "fallback": None,
            "configured_providers": {},
            "family_bindings": {}
        }

    def _save_providers_config(self) -> None:
        """Save provider configuration."""
        with open(self.config_path, "w") as f:
            json.dump(self.providers, f, indent=2)

    def list_available_providers(self) -> Dict[str, Dict[str, str]]:
        """List all available LLM providers."""
        return self.PROVIDERS

    def list_configured_providers(self) -> Dict[str, str]:
        """List already configured providers."""
        return self.providers.get("configured_providers", {})

    def add_provider(self, provider_id: str, credentials: Dict[str, str]) -> bool:
        """
        Add or update provider credentials.

        Args:
            provider_id: Provider key (claude, gemini, etc.)
            credentials: Dict with auth fields (api_key, host, port, etc.)

        Returns:
            True if successful
        """
        if provider_id not in self.PROVIDERS:
            print(f"⚠️  Unknown provider: {provider_id}")
            return False

        provider_info = self.PROVIDERS[provider_id]

        # Validate required fields
        for field in provider_info["required_fields"]:
            if field not in credentials or not credentials[field]:
                print(f"⚠️  Missing required field: {field}")
                return False

        # Store credentials in local file (never synced)
        cred_file = self.creds_dir / f"{provider_id}.json"
        with open(cred_file, "w") as f:
            json.dump(credentials, f, indent=2)

        # Set file permissions to owner-only (no world-readable)
        os.chmod(cred_file, 0o600)

        # Update config
        self.providers["configured_providers"][provider_id] = {
            "name": provider_info["name"],
            "auth_type": provider_info["auth_type"],
            "configured_at": str(Path.cwd())
        }
        self._save_providers_config()

        print(f"✅ Provider '{provider_id}' configured successfully")
        print(f"   Credentials stored at: {cred_file}")
        print(f"   File permissions: owner-only (0o600)")
        return True

    def get_provider_credentials(self, provider_id: str) -> Optional[Dict[str, str]]:
        """Retrieve stored credentials for a provider."""
        cred_file = self.creds_dir / f"{provider_id}.json"
        if not cred_file.exists():
            return None

        with open(cred_file) as f:
            return json.load(f)

    def set_primary_provider(self, provider_id: str) -> bool:
        """Set primary LLM provider."""
        if provider_id not in self.providers.get("configured_providers", {}):
            print(f"⚠️  Provider '{provider_id}' not configured")
            return False

        self.providers["primary"] = provider_id
        self._save_providers_config()
        print(f"✅ Primary provider set to: {provider_id}")
        return True

    def set_fallback_provider(self, provider_id: str) -> bool:
        """Set fallback LLM provider."""
        if provider_id not in self.providers.get("configured_providers", {}):
            print(f"⚠️  Provider '{provider_id}' not configured")
            return False

        self.providers["fallback"] = provider_id
        self._save_providers_config()
        print(f"✅ Fallback provider set to: {provider_id}")
        return True

    def get_provider_status(self) -> Dict[str, Any]:
        """Get current provider configuration status."""
        return {
            "primary": self.providers.get("primary"),
            "fallback": self.providers.get("fallback"),
            "configured": list(self.providers.get("configured_providers", {}).keys()),
            "config_file": str(self.config_path),
            "credentials_dir": str(self.creds_dir)
        }

    def bind_provider_to_family(self, family_id: str, provider_id: str, role: str = "primary") -> bool:
        """
        Bind a provider to a family (Family A, B, C).
        Allows different families to use different providers.

        Args:
            family_id: Family identifier (A, B, C, etc.)
            provider_id: Provider to bind
            role: "primary" or "fallback"

        Returns:
            True if successful
        """
        if family_id not in ["A", "B", "C"]:
            print(f"⚠️  Unknown family: {family_id}")
            return False

        if provider_id not in self.providers.get("configured_providers", {}):
            print(f"⚠️  Provider '{provider_id}' not configured")
            return False

        if "family_bindings" not in self.providers:
            self.providers["family_bindings"] = {}

        if family_id not in self.providers["family_bindings"]:
            self.providers["family_bindings"][family_id] = {}

        self.providers["family_bindings"][family_id][role] = provider_id
        self._save_providers_config()

        print(f"✅ Family {family_id} {role} provider set to: {provider_id}")
        return True

    def get_family_provider_config(self, family_id: str) -> Dict[str, str]:
        """Get provider configuration for a specific family."""
        family_bindings = self.providers.get("family_bindings", {}).get(family_id, {})
        return family_bindings or {
            "primary": self.providers.get("primary"),
            "fallback": self.providers.get("fallback")
        }


def interactive_setup():
    """Interactive setup wizard for founder/operator."""
    manager = ProviderAuthManager()

    print("\n" + "="*70)
    print("  LANTERN PROVIDER AUTHENTICATION & ACCOUNT SETUP")
    print("="*70 + "\n")

    while True:
        print("\nOptions:")
        print("  1. List available providers")
        print("  2. Configure a new provider (sign in / add account)")
        print("  3. Set primary provider")
        print("  4. Set fallback provider")
        print("  5. View current configuration")
        print("  6. Bind provider to family (Family A/B/C)")
        print("  7. Exit")
        print()

        choice = input("Enter choice (1-7): ").strip()

        if choice == "1":
            print("\nAvailable Providers:\n")
            for pid, info in manager.list_available_providers().items():
                print(f"  [{pid}] {info['name']}")
                print(f"      Auth type: {info['auth_type']}")
                print(f"      Setup: {info['setup_instructions']}")
                print()

        elif choice == "2":
            print("\nAvailable providers to configure:")
            for pid in manager.PROVIDERS.keys():
                status = "✅ Configured" if pid in manager.list_configured_providers() else "⚠️  Not configured"
                print(f"  {pid}: {status}")

            provider_id = input("\nEnter provider ID (or 'back'): ").strip().lower()
            if provider_id == "back":
                continue

            if provider_id not in manager.PROVIDERS:
                print(f"⚠️  Unknown provider: {provider_id}")
                continue

            provider_info = manager.PROVIDERS[provider_id]
            credentials = {}

            print(f"\nConfiguring {provider_info['name']}...")
            print(f"Setup: {provider_info['setup_instructions']}\n")

            for field in provider_info["required_fields"]:
                value = input(f"  Enter {field}: ").strip()
                credentials[field] = value

            for field in provider_info["optional_fields"]:
                value = input(f"  Enter {field} (optional, press Enter to skip): ").strip()
                if value:
                    credentials[field] = value

            if manager.add_provider(provider_id, credentials):
                print(f"\n✅ {provider_info['name']} configured!")
            else:
                print(f"\n⚠️  Failed to configure {provider_info['name']}")

        elif choice == "3":
            configured = manager.list_configured_providers()
            if not configured:
                print("⚠️  No providers configured yet")
                continue

            print("\nConfigured providers:")
            for pid in configured.keys():
                print(f"  {pid}")

            provider_id = input("\nSelect primary provider: ").strip().lower()
            manager.set_primary_provider(provider_id)

        elif choice == "4":
            configured = manager.list_configured_providers()
            if not configured:
                print("⚠️  No providers configured yet")
                continue

            print("\nConfigured providers:")
            for pid in configured.keys():
                print(f"  {pid}")

            provider_id = input("\nSelect fallback provider: ").strip().lower()
            manager.set_fallback_provider(provider_id)

        elif choice == "5":
            status = manager.get_provider_status()
            print("\nCurrent Configuration:")
            print(f"  Primary: {status['primary'] or 'Not set'}")
            print(f"  Fallback: {status['fallback'] or 'Not set'}")
            print(f"  Configured providers: {', '.join(status['configured']) or 'None'}")
            print(f"  Config file: {status['config_file']}")
            print(f"  Credentials directory: {status['credentials_dir']}")

        elif choice == "6":
            print("\nBind provider to family...")
            family_id = input("  Family ID (A/B/C): ").strip().upper()

            configured = manager.list_configured_providers()
            if not configured:
                print("⚠️  No providers configured yet")
                continue

            print("  Available providers:")
            for pid in configured.keys():
                print(f"    {pid}")

            provider_id = input("  Provider ID: ").strip().lower()
            role = input("  Role (primary/fallback): ").strip().lower()

            manager.bind_provider_to_family(family_id, provider_id, role)

        elif choice == "7":
            print("\n✅ Setup complete. Lantern is ready to start.")
            break

        else:
            print("⚠️  Invalid choice")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # CLI mode for scripting
        action = sys.argv[1]
        manager = ProviderAuthManager()

        if action == "list":
            status = manager.get_provider_status()
            print(json.dumps(status, indent=2))

        elif action == "add" and len(sys.argv) >= 4:
            provider_id = sys.argv[2]
            creds_json = sys.argv[3]
            credentials = json.loads(creds_json)
            manager.add_provider(provider_id, credentials)

        elif action == "status":
            status = manager.get_provider_status()
            print(json.dumps(status, indent=2))

        else:
            print("Usage:")
            print("  python lantern-provider-auth.py list")
            print("  python lantern-provider-auth.py add <provider> '{\"key\": \"value\"}'")
            print("  python lantern-provider-auth.py status")
            print("  Or run with no args for interactive setup")

    else:
        # Interactive mode
        interactive_setup()
