#!/usr/bin/env python3
"""
Lantern Chat Interface - Real-time chat with local LLMs (with M5 Capability Attestation)

Connects to LM Studio (1234) or Ollama (11434) for inference.
Displays messages in real-time as they arrive.
Includes M5 (Runtime Attestation) to continuously prove capability with timestamp evidence.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import os

# Import M5 capability attestation
try:
    from lantern_capability_attestation import CapabilityAttestation
    M5_AVAILABLE = True
except ImportError:
    M5_AVAILABLE = False

# Optional: Audio support for Music player
try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Optional: RetroArch gaming
RETROARCH_PATH = Path("D:\\Games\\RetroarchWin\\retroarch.exe")
RETROARCH_AVAILABLE = RETROARCH_PATH.exists()


class LanternChat:
    """Real-time chat interface for Lantern."""

    def __init__(self, root, selected_provider: str = "lm_studio"):
        self.root = root
        self.selected_provider = selected_provider
        self.root.title("Lantern Chat")
        self.root.geometry("900x700")

        # Load config
        self.config = self._load_config()
        self.current_model = self.config["llm_providers"][selected_provider]["config"].get("model", "local")

        # Accessibility: Load user preferences
        self.font_size = self._load_font_size()
        self.font_family = self._load_font_family()

        # M5 Capability Attestation (Phase 1 implementation)
        self.attestation = None
        if M5_AVAILABLE:
            try:
                self.attestation = CapabilityAttestation()
                # Start continuous attestation in background (5-minute interval)
                providers_config = self._extract_provider_configs()
                self.attestation.start_continuous_attestation(providers_config)
            except Exception as e:
                print(f"[M5] Warning: Attestation initialization failed: {e}")

        # UI Elements
        self._build_ui()

        self.message_count = 0
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _load_font_size(self) -> int:
        """Load font size preference (default 10pt)."""
        try:
            prefs_path = Path.home() / ".lantern" / "user-prefs.json"
            if prefs_path.exists():
                with open(prefs_path) as f:
                    prefs = json.load(f)
                    return prefs.get("font_size", 10)
        except:
            pass
        return 10

    def _load_font_family(self) -> str:
        """Load font family preference (default Consolas)."""
        try:
            prefs_path = Path.home() / ".lantern" / "user-prefs.json"
            if prefs_path.exists():
                with open(prefs_path) as f:
                    prefs = json.load(f)
                    return prefs.get("font_family", "Consolas")
        except:
            pass
        return "Consolas"

    def _save_preferences(self):
        """Save font preferences to disk."""
        prefs_path = Path.home() / ".lantern" / "user-prefs.json"
        prefs_path.parent.mkdir(parents=True, exist_ok=True)
        with open(prefs_path, 'w') as f:
            json.dump({
                "font_size": self.font_size,
                "font_family": self.font_family
            }, f, indent=2)

    def _load_config(self):
        """Load LLM configuration."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            return json.load(f)

    def _extract_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        """Extract provider configurations for M5 attestation."""
        providers = {}
        try:
            for provider_name, provider_cfg in self.config.get("llm_providers", {}).items():
                # Pass the full provider config, not just the "config" sub-dict
                providers[provider_name] = provider_cfg
        except Exception as e:
            print(f"[M5] Warning: Failed to extract provider configs: {e}")
        return providers

    def _build_ui(self):
        """Build unified Lantern interface with Chat and Music tabs."""
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(header, text="Lantern", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text=f"Model: {self.current_model}", font=("Segoe UI", 9), foreground="gray").pack(side=tk.RIGHT)

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Chat tab
        chat_tab = ttk.Frame(self.notebook)
        self.notebook.add(chat_tab, text="Chat")
        self._build_chat_tab(chat_tab)

        # Music tab
        music_tab = ttk.Frame(self.notebook)
        self.notebook.add(music_tab, text="Music")
        self._build_music_tab(music_tab)

        # Status bar (shared)
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=2)
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, font=("Segoe UI", 8))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.capability_label = ttk.Label(status_frame, text="● Operational", font=("Segoe UI", 8))
        self.capability_label.pack(side=tk.RIGHT, padx=(10, 0))

    def _build_chat_tab(self, parent):
        """Build Chat tab UI."""
        # Accessibility settings
        settings = ttk.Frame(parent)
        settings.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(settings, text="Text Size:", font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 5))
        size_var = tk.IntVar(value=self.font_size)
        size_combo = ttk.Combobox(settings, textvariable=size_var, values=[10, 12, 14, 16, 18], width=5, state="readonly")
        size_combo.pack(side=tk.LEFT, padx=(0, 15))
        size_combo.bind("<<ComboboxSelected>>", lambda e: self._update_font_size(int(size_var.get())))

        ttk.Label(settings, text="Font:", font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 5))
        family_var = tk.StringVar(value=self.font_family)
        family_combo = ttk.Combobox(settings, textvariable=family_var, values=["Consolas", "Arial", "Courier"], width=10, state="readonly")
        family_combo.pack(side=tk.LEFT, padx=(0, 15))
        family_combo.bind("<<ComboboxSelected>>", lambda e: self._update_font_family(family_var.get()))

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, state=tk.DISABLED,
            font=(self.font_family, self.font_size),
            bg="#1e1e1e", fg="#e0e0e0", highlightthickness=2, highlightcolor="#00ff88"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.chat_display.tag_config("user", foreground="#00ff88", font=(self.font_family, self.font_size, "bold"))
        self.chat_display.tag_config("bot", foreground="#00ccff", font=(self.font_family, self.font_size))
        self.chat_display.tag_config("timestamp", foreground="#666666", font=(self.font_family, self.font_size - 2))
        self.chat_display.tag_config("error", foreground="#ff6b6b", font=(self.font_family, self.font_size))

        # Input frame
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        self.input_field = tk.Text(input_frame, height=4, font=(self.font_family, self.font_size),
                                   bg="#2d2d2d", fg="#e0e0e0", highlightthickness=2, highlightcolor="#00ff88")
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_field.bind("<Control-Return>", lambda e: self.send_message())

        send_btn = tk.Button(input_frame, text="Send\n(Ctrl+Enter)", command=self.send_message,
                             width=14, height=2, padx=10, pady=10,
                             bg="#1e1e1e", fg="#00ff88", activebackground="#2d2d2d", activeforeground="#00ff88",
                             relief=tk.RAISED, bd=2, highlightthickness=3, highlightcolor="#ffff00",
                             font=("Segoe UI", 10, "bold"))
        send_btn.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        # Startup messages
        self._display_message("Lantern", f"Connected to {self.current_model} on {self.selected_provider}", "bot")
        if M5_AVAILABLE:
            self._display_message("System", "M5 Attestation active (tests every 5 minutes)", "bot")

    def _build_music_tab(self, parent):
        """Build Music tab with integrated player."""
        # Header
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(header, text="Curated Soundscape", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)

        # Sound list
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sound_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        font=(self.font_family, 10),
                                        bg="#2d2d2d", fg="#e0e0e0", selectmode=tk.SINGLE)
        self.sound_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sound_listbox.yview)
        self._load_sound_library()

        # Controls
        control = ttk.Frame(parent)
        control.pack(fill=tk.X, padx=10, pady=5)

        play_btn = tk.Button(control, text="▶ Play", command=self._play_selected_sound,
                            width=12, height=1, bg="#1e1e1e", fg="#00ff88", activebackground="#2d2d2d",
                            font=("Segoe UI", 10, "bold"))
        play_btn.pack(side=tk.LEFT, padx=(0, 5))

        stop_btn = tk.Button(control, text="⏹ Stop", command=self._stop_sound,
                            width=12, height=1, bg="#1e1e1e", fg="#ff6b6b", activebackground="#2d2d2d",
                            font=("Segoe UI", 10, "bold"))
        stop_btn.pack(side=tk.LEFT)

        self.music_status = ttk.Label(parent, text="Ready to play", font=("Segoe UI", 9), foreground="gray")
        self.music_status.pack(padx=10, pady=5)

    def _load_sound_library(self):
        """Load available sounds from ~/.lantern/sounds/."""
        sounds_dir = Path.home() / ".lantern" / "sounds"
        self.sound_files = {}

        if sounds_dir.exists():
            for audio_file in sorted(sounds_dir.glob("*.ogg")) + sorted(sounds_dir.glob("*.wav")):
                display_name = audio_file.stem.replace("_", " ").title()
                self.sound_listbox.insert(tk.END, display_name)
                self.sound_files[display_name] = str(audio_file)

    def _play_selected_sound(self):
        """Play selected sound from listbox."""
        selection = self.sound_listbox.curselection()
        if not selection:
            self.music_status.config(text="Please select a sound", foreground="#ff6b6b")
            return

        display_name = self.sound_listbox.get(selection[0])
        sound_path = self.sound_files.get(display_name)

        if not sound_path:
            self.music_status.config(text="Sound file not found", foreground="#ff6b6b")
            return

        if not AUDIO_AVAILABLE:
            self.music_status.config(text="Audio support not available (install pygame)", foreground="#ff6b6b")
            return

        try:
            self.music_status.config(text=f"Playing: {display_name}...", foreground="#00ff88")
            self.root.update()

            pygame.mixer.init()
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
        except Exception as e:
            self.music_status.config(text=f"Error: {str(e)[:40]}", foreground="#ff6b6b")

    def _stop_sound(self):
        """Stop playback."""
        if AUDIO_AVAILABLE:
            pygame.mixer.music.stop()
            self.music_status.config(text="Stopped", foreground="#666666")

    def _display_message(self, sender: str, text: str, msg_type: str = "user"):
        """Display message in chat (real-time)."""
        self.chat_display.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{sender}: ", msg_type)
        self.chat_display.insert(tk.END, f"{text}\n", msg_type)
        self.chat_display.insert(tk.END, "\n")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.root.update()

    def _stream_response(self, text: str, msg_type: str = "bot"):
        """Stream response word-by-word (real-time effect)."""
        self.chat_display.config(state=tk.NORMAL)
        words = text.split()

        for i, word in enumerate(words):
            self.chat_display.insert(tk.END, word + " ", msg_type)
            if i % 5 == 0:  # Update display every 5 words
                self.chat_display.config(state=tk.DISABLED)
                self.chat_display.see(tk.END)
                self.root.update()
                self.chat_display.config(state=tk.NORMAL)

        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def send_message(self):
        """Send message to LLM and get response."""
        user_input = self.input_field.get("1.0", tk.END).strip()

        if not user_input:
            return

        # Clear input
        self.input_field.delete("1.0", tk.END)

        # Display user message
        self._display_message("You", user_input, "user")
        self.status_label.config(text="Thinking...")
        self.message_count += 1

        # Get LLM response in background thread
        thread = threading.Thread(target=self._get_llm_response, args=(user_input,), daemon=True)
        thread.start()

    def _get_llm_response(self, prompt: str):
        """Get response from local LLM (real-time streaming)."""
        try:
            endpoint = self.config["llm_providers"][self.selected_provider]["endpoint"]

            # Prepare request
            payload = {
                "model": self.current_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 512
            }

            # For local endpoints, add generous timeout (first inference can be slow)
            response = requests.post(
                endpoint,
                json=payload,
                stream=True,
                timeout=120
            )

            if response.status_code != 200:
                self._display_message("Error", f"API returned {response.status_code}", "error")
                self.status_label.config(text=f"Error: {response.status_code}")
                return

            # Stream response
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.chat_display.insert(tk.END, "Lantern: ", "bot")
            self.chat_display.config(state=tk.DISABLED)

            full_response = ""

            # Handle streaming response
            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')

                    if line.startswith("data: "):
                        line = line[6:]

                    if not line or line == "[DONE]":
                        continue

                    data = json.loads(line)

                    # Extract text based on API format
                    if "choices" in data:
                        choice = data["choices"][0]
                        if "delta" in choice and "content" in choice["delta"]:
                            token = choice["delta"]["content"]
                        elif "text" in choice:
                            token = choice["text"]
                        else:
                            continue
                    else:
                        continue

                    full_response += token

                    # Display token in real-time
                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.insert(tk.END, token, "bot")
                    self.chat_display.config(state=tk.DISABLED)
                    self.chat_display.see(tk.END)
                    self.root.update()

                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON decode error: {e}, line: {line[:100]}")
                    continue
                except KeyError as e:
                    print(f"[DEBUG] Missing key in response: {e}")
                    continue

            # End of message
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.config(state=tk.DISABLED)

            self.status_label.config(text=f"Ready ({self.message_count} messages)")

        except requests.exceptions.ConnectionError:
            endpoint = self.config['llm_providers'][self.selected_provider]['endpoint']
            self._display_message(
                "Error",
                f"Cannot connect to {self.selected_provider}\nEndpoint: {endpoint}\n\nTROUBLESHOOT:\n1. Is LM Studio running on port 1234?\n2. Is Ollama running on port 11434?\n3. Check firewall settings\n\nTrying fallback provider...",
                "error"
            )
            self.status_label.config(text="Connection failed - trying fallback")
            self._try_fallback_provider(prompt)
        except Exception as e:
            self._display_message("Error", f"Exception: {str(e)}", "error")
            self.status_label.config(text=f"Error: {str(e)[:40]}")

    def _try_fallback_provider(self, prompt: str):
        """Try alternative provider if primary fails."""
        fallback_chain = ["ollama", "lm_studio"]  # Try Ollama, then LM Studio

        for provider in fallback_chain:
            if provider == self.selected_provider:
                continue

            try:
                self._display_message("Fallback", f"Trying {provider}...", "bot")
                self.selected_provider = provider
                self.current_model = self.config["llm_providers"][provider]["config"].get("model", "local")

                # Retry the request
                self._get_llm_response(prompt)
                return
            except Exception as e:
                print(f"Fallback to {provider} also failed: {e}")
                continue

        self._display_message("Error", "All LLM providers unavailable. Please check system status.", "error")
        self.status_label.config(text="CRITICAL: All providers offline")

    def _update_font_size(self, new_size: int):
        """Update font size for accessibility."""
        self.font_size = new_size
        self.chat_display.config(font=(self.font_family, self.font_size))
        self.input_field.config(font=(self.font_family, self.font_size))

        # Update tags
        self.chat_display.tag_config("user", font=(self.font_family, self.font_size, "bold"))
        self.chat_display.tag_config("bot", font=(self.font_family, self.font_size))
        self.chat_display.tag_config("timestamp", font=(self.font_family, max(self.font_size - 2, 8)))
        self.chat_display.tag_config("error", font=(self.font_family, self.font_size))

        self._save_preferences()

    def _update_font_family(self, new_family: str):
        """Update font family for dyslexia accessibility."""
        self.font_family = new_family
        self.chat_display.config(font=(self.font_family, self.font_size))
        self.input_field.config(font=(self.font_family, self.font_size))

        # Update tags
        self.chat_display.tag_config("user", font=(self.font_family, self.font_size, "bold"))
        self.chat_display.tag_config("bot", font=(self.font_family, self.font_size))
        self.chat_display.tag_config("timestamp", font=(self.font_family, max(self.font_size - 2, 8)))
        self.chat_display.tag_config("error", font=(self.font_family, self.font_size))

        self._save_preferences()

    def _update_capability_status(self):
        """Update M5 capability indicator in status bar (runs periodically)."""
        if not self.attestation or not self.capability_label:
            return

        try:
            status = self.attestation.get_capability_status(self.selected_provider)
            provider_state = status.get(self.selected_provider, {})

            capability_status = provider_state.get("status", "unknown")
            failure_count = provider_state.get("failure_count", 0)

            if capability_status == "operational":
                indicator = "● Operational"
                color_prefix = ""
            elif capability_status == "degraded":
                indicator = f"⚠ Degraded ({failure_count} failures)"
                color_prefix = "warning"
            else:
                indicator = "○ Unknown"
                color_prefix = "gray"

            self.capability_label.config(text=indicator)
        except Exception as e:
            print(f"[M5] Error updating capability status: {e}")

    def _on_window_close(self):
        """Handle window close event (stop M5 attestation and cleanup)."""
        try:
            if self.attestation:
                self.attestation.stop_continuous_attestation()
                print("[M5] Attestation stopped on window close")
        except Exception as e:
            print(f"[M5] Warning on close: {e}")

        self.root.destroy()


def main():
    """Launch Lantern Chat."""
    root = tk.Tk()
    chat = LanternChat(root, selected_provider="lm_studio")  # Default to LM Studio
    root.mainloop()


if __name__ == "__main__":
    main()
