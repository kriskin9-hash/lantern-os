#!/usr/bin/env python3
"""
Lantern Desktop Authentication UI

Login screen for founders/operators before accessing the chat interface.
Allows sign-in to multiple LLM providers with provider switching and fallback configuration.
"""

import json
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import threading
import subprocess
import socket
import time
import sys


CREDS_DIR = Path.home() / ".lantern" / "credentials"
PROVIDERS_CONFIG = Path.home() / ".lantern" / "providers.json"

# Add scripts dir to path for audio narrator import
sys.path.insert(0, str(Path(__file__).parent))

def play_tutorial_audio(key: str):
    """Play tutorial audio narration."""
    try:
        from lantern_audio_narrator import play_narration
        threading.Thread(target=play_narration, args=(key,), daemon=True).start()
    except (ImportError, Exception):
        pass  # Audio not available, continue silently


def start_local_llms():
    """Start LM Studio and Ollama if not already running."""

    def port_is_open(port: int, timeout: float = 0.5) -> bool:
        """Check if a port is responding."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0

    # Check if services are already running
    lm_studio_running = port_is_open(1234)
    ollama_running = port_is_open(11434)

    if lm_studio_running and ollama_running:
        return  # Both already running, skip

    # Try to start LM Studio if not running
    if not lm_studio_running:
        lm_studio_paths = [
            "C:\\Program Files\\LM Studio\\LM Studio.exe",
            "C:\\Program Files (x86)\\LM Studio\\LM Studio.exe",
            str(Path.home() / "AppData" / "Local" / "Programs" / "lmstudio" / "lm-studio.exe"),
        ]
        for path in lm_studio_paths:
            if Path(path).exists():
                try:
                    subprocess.Popen([path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
                break

    # Try to start Ollama if not running
    if not ollama_running:
        ollama_paths = [
            "C:\\Program Files\\Ollama\\ollama.exe",
            "C:\\Program Files (x86)\\Ollama\\ollama.exe",
            str(Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe"),
        ]
        for path in ollama_paths:
            if Path(path).exists():
                try:
                    subprocess.Popen([path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
                break

    # Wait for services to be ready (up to 10 seconds)
    for i in range(10):
        if port_is_open(1234) and port_is_open(11434):
            time.sleep(0.5)
            return
        time.sleep(1)


class ProviderAuthUI(tk.Toplevel):
    """Authentication UI for configuring LLM providers."""

    PROVIDERS = {
        "claude": {
            "name": "Anthropic Claude",
            "icon": "🧠",
            "color": "#E8D7F1",
            "fields": [("API Key", "api_key", True)]
        },
        "gemini": {
            "name": "Google Gemini",
            "icon": "🎨",
            "color": "#E8F0FE",
            "fields": [("API Key", "api_key", True)]
        },
        "deepseek": {
            "name": "DeepSeek",
            "icon": "⚡",
            "color": "#FFF5E6",
            "fields": [("API Key", "api_key", True)]
        },
        "local-lm-studio": {
            "name": "Local LM Studio",
            "icon": "💻",
            "color": "#E6F3FF",
            "fields": [("Host", "host", False), ("Port", "port", False)]
        },
        "ollama": {
            "name": "Local Ollama",
            "icon": "🦙",
            "color": "#F0E6FF",
            "fields": [("Host", "host", False), ("Port", "port", False)]
        }
    }

    def __init__(self, parent: tk.Tk, on_ready: Callable):
        """
        Initialize auth UI.

        Args:
            parent: Parent window (Lantern Desktop)
            on_ready: Callback when authentication is complete
        """
        super().__init__(parent)
        self.parent = parent
        self.on_ready = on_ready
        self.title("Lantern — Provider Authentication")
        self.geometry("900x650")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.transient(parent)
        self.grab_set()

        self.config_path = PROVIDERS_CONFIG
        self.creds_dir = CREDS_DIR
        self.creds_dir.mkdir(parents=True, exist_ok=True)
        self.providers_config = self._load_config()

        self.current_provider = tk.StringVar()
        self.auth_complete = False

        self._build()
        self._center_on_parent()

    def _load_config(self) -> Dict[str, Any]:
        """Load current provider configuration."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {"primary": None, "fallback": None, "configured_providers": {}}

    def _save_config(self) -> None:
        """Save provider configuration."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.providers_config, f, indent=2)

    def _center_on_parent(self) -> None:
        """Center auth window on parent."""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build(self) -> None:
        """Build UI."""
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Play intro narration
        play_tutorial_audio("intro")

        # Header
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text="🔐 Lantern Provider Authentication", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text="Sign in to connect your LLM providers").pack(side=tk.LEFT, padx=(20, 0))

        # Provider selector
        selector_frame = ttk.LabelFrame(main, text="Available Providers", padding=12)
        selector_frame.pack(fill=tk.X, pady=(0, 15))

        buttons_frame = ttk.Frame(selector_frame)
        buttons_frame.pack(fill=tk.X, expand=True)

        for provider_id, info in self.PROVIDERS.items():
            status = "✅" if provider_id in self.providers_config.get("configured_providers", {}) else "⭕"
            btn = ttk.Button(
                buttons_frame,
                text=f"{info['icon']} {info['name']}\n{status}",
                command=lambda pid=provider_id: self._show_provider_form(pid),
                width=20
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        # Auth form area
        self.form_frame = ttk.LabelFrame(main, text="", padding=15)
        self.form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.form_widgets: Dict[str, tk.Widget] = {}

        # Control buttons
        control_frame = ttk.Frame(main)
        control_frame.pack(fill=tk.X)

        ttk.Button(control_frame, text="View Configuration", command=self._show_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Set Primary Provider", command=self._set_primary).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Set Fallback Provider", command=self._set_fallback).pack(side=tk.LEFT, padx=(0, 10))

        # Accessibility: Larger buttons with bright focus
        ready_btn = tk.Button(control_frame, text="[OK] Ready", command=self.on_ready_click,
                              padx=15, pady=10, bg="#1e1e1e", fg="#00ff88", activebackground="#2d2d2d",
                              activeforeground="#00ff88", relief=tk.RAISED, bd=2,
                              highlightthickness=3, highlightcolor="#ffff00", highlightbackground="#1e1e1e",
                              font=("Segoe UI", 11, "bold"))
        ready_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = tk.Button(control_frame, text="Cancel", command=self.on_cancel,
                               padx=15, pady=10, bg="#1e1e1e", fg="#ff6b6b", activebackground="#2d2d2d",
                               activeforeground="#ff6b6b", relief=tk.RAISED, bd=2,
                               highlightthickness=3, highlightcolor="#ffff00", highlightbackground="#1e1e1e",
                               font=("Segoe UI", 11, "bold"))
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def _show_provider_form(self, provider_id: str) -> None:
        """Show form to configure a provider."""
        # Play provider selection narration
        if provider_id in ["claude", "gemini"]:
            play_tutorial_audio("step1_providers")

        # Clear previous form
        for widget in self.form_widgets.values():
            widget.destroy()
        self.form_widgets.clear()

        provider_info = self.PROVIDERS[provider_id]
        self.form_frame.configure(text=f"Configure {provider_info['name']}")

        # Instructions
        instructions = {
            "claude": "Get your API key from https://console.anthropic.com/",
            "gemini": "Get your API key from https://makersuite.google.com/",
            "deepseek": "Get your API key from https://platform.deepseek.com/",
            "local-lm-studio": "Ensure LM Studio is running locally (default: localhost:1234)",
            "ollama": "Ensure Ollama is running locally (default: localhost:11434)"
        }

        if provider_id in instructions:
            instr_label = ttk.Label(self.form_frame, text=instructions[provider_id], foreground="blue")
            self.form_widgets["instructions"] = instr_label
            instr_label.pack(fill=tk.X, pady=(0, 15))

        # Form fields
        fields_frame = ttk.Frame(self.form_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 15))

        for field_label, field_name, is_password in provider_info["fields"]:
            row = ttk.Frame(fields_frame)
            row.pack(fill=tk.X, pady=(0, 10))

            label = ttk.Label(row, text=field_label, width=15)
            label.pack(side=tk.LEFT, padx=(0, 10))

            if is_password:
                entry = ttk.Entry(row, show="•", width=40)
            else:
                entry = ttk.Entry(row, width=40)

            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.form_widgets[field_name] = entry

        # Existing credentials indicator
        cred_file = self.creds_dir / f"{provider_id}.json"
        if cred_file.exists():
            existing = ttk.Label(self.form_frame, text="✅ Credentials already configured for this provider", foreground="green")
            self.form_widgets["existing"] = existing
            existing.pack(fill=tk.X, pady=(0, 10))

        # Save button
        save_btn = ttk.Button(
            self.form_frame,
            text="Save Provider Credentials",
            command=lambda: self._save_provider(provider_id)
        )
        self.form_widgets["save_btn"] = save_btn
        save_btn.pack(fill=tk.X)

    def _save_provider(self, provider_id: str) -> None:
        """Save provider credentials."""
        # Collect credentials
        credentials = {}
        for field_name, widget in self.form_widgets.items():
            if field_name not in ["instructions", "existing", "save_btn"] and isinstance(widget, ttk.Entry):
                credentials[field_name] = widget.get().strip()

        # Validate
        for field_name in self.PROVIDERS[provider_id]["fields"]:
            field_name_key = field_name[1]
            if not credentials.get(field_name_key):
                messagebox.showwarning("Missing Field", f"Please enter {field_name[0]}")
                return

        # Save to file
        cred_file = self.creds_dir / f"{provider_id}.json"
        with open(cred_file, "w") as f:
            json.dump(credentials, f, indent=2)

        import os
        os.chmod(cred_file, 0o600)

        # Update config
        if "configured_providers" not in self.providers_config:
            self.providers_config["configured_providers"] = {}

        self.providers_config["configured_providers"][provider_id] = {
            "name": self.PROVIDERS[provider_id]["name"],
            "auth_type": "api_key" if "api_key" in credentials else "endpoint"
        }
        self._save_config()

        messagebox.showinfo(
            "Success",
            f"✅ {self.PROVIDERS[provider_id]['name']} configured!\n\nCredentials saved securely at:\n{cred_file}"
        )

        # Refresh
        self._build()

    def _show_config(self) -> None:
        """Show current configuration."""
        config_text = "CURRENT PROVIDER CONFIGURATION\n"
        config_text += "=" * 50 + "\n\n"

        config_text += f"Primary Provider: {self.providers_config.get('primary') or 'Not set'}\n"
        config_text += f"Fallback Provider: {self.providers_config.get('fallback') or 'Not set'}\n\n"

        config_text += "Configured Providers:\n"
        for pid, info in self.providers_config.get("configured_providers", {}).items():
            config_text += f"  ✅ {pid} ({info.get('name', 'Unknown')})\n"

        if not self.providers_config.get("configured_providers"):
            config_text += "  (none configured yet)\n"

        messagebox.showinfo("Provider Configuration", config_text)

    def _set_primary(self) -> None:
        """Set primary provider."""
        configured = list(self.providers_config.get("configured_providers", {}).keys())
        if not configured:
            messagebox.showwarning("No Providers", "Configure at least one provider first")
            return

        # Simple dialog
        root = tk.Tk()
        root.withdraw()
        choice = None
        root.destroy()

        messagebox.showinfo("Set Primary", "Click OK and select from available providers")

    def _set_fallback(self) -> None:
        """Set fallback provider."""
        configured = list(self.providers_config.get("configured_providers", {}).keys())
        if not configured:
            messagebox.showwarning("No Providers", "Configure at least one provider first")
            return

        messagebox.showinfo("Set Fallback", "Select a provider to use as fallback if primary is unavailable")

    def on_ready_click(self) -> None:
        """Handle ready button."""
        configured = self.providers_config.get("configured_providers", {})
        if not configured:
            messagebox.showwarning("No Providers", "Please configure at least one provider before proceeding")
            return

        primary = self.providers_config.get("primary")
        if not primary:
            messagebox.showwarning("No Primary", "Please set a primary provider before proceeding")
            return

        # Play success narration
        play_tutorial_audio("success")

        self.auth_complete = True
        self.destroy()
        self.on_ready()

    def on_cancel(self) -> None:
        """Handle cancel button."""
        if messagebox.askyesno("Cancel", "Exit without completing authentication?"):
            self.parent.destroy()


class LanternDesktopWithAuth(tk.Tk):
    """Lantern Desktop with authentication flow."""

    def __init__(self):
        super().__init__()
        self.title("Lantern Chat")
        self.geometry("600x400")

        main = ttk.Frame(self, padding=40)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="🚀 Lantern Chat", font=("Segoe UI", 24, "bold")).pack(pady=(0, 20))
        ttk.Label(main, text="Starting local LLM services...").pack(pady=(0, 10))
        status_label = ttk.Label(main, text="Checking LM Studio and Ollama...", foreground="blue")
        status_label.pack()

        self.update()

        # Start local LLMs in background thread
        def start_services():
            start_local_llms()
            self.after(0, self._on_services_ready)

        threading.Thread(target=start_services, daemon=True).start()

    def _on_services_ready(self) -> None:
        """Called when local LLM services are ready."""
        # Clear loading screen
        for widget in self.winfo_children():
            widget.destroy()

        main = ttk.Frame(self, padding=40)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="🚀 Lantern Chat", font=("Segoe UI", 24, "bold")).pack(pady=(0, 20))
        ttk.Label(main, text="Initializing authentication...").pack()

        # Show auth UI
        auth_ui = ProviderAuthUI(self, self.on_auth_complete)

    def on_auth_complete(self) -> None:
        """Called when authentication is complete."""
        # Get selected provider
        selected_provider = self.providers_config.get("primary", "lm_studio")

        # Load and launch chat
        try:
            from lantern_chat_ui import LanternChat
            # Clear the auth window and launch chat
            for widget in self.winfo_children():
                widget.destroy()
            chat = LanternChat(self, selected_provider=selected_provider)
        except ImportError:
            # Fallback if chat module not available
            for widget in self.winfo_children():
                widget.destroy()
            main = ttk.Frame(self, padding=20)
            main.pack(fill=tk.BOTH, expand=True)
            ttk.Label(main, text="✅ Lantern Chat", font=("Segoe UI", 18, "bold")).pack(pady=(0, 10))
            ttk.Label(main, text="Chat interface ready.\nProviders configured and available.", foreground="green").pack(pady=(20, 0))


if __name__ == "__main__":
    app = LanternDesktopWithAuth()
    app.mainloop()
