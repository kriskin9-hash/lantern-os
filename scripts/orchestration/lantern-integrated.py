#!/usr/bin/env python3
"""
Lantern Integrated Platform - All-in-one unified interface
Chat | Music | Games | Browser | Email | Videos | Reminders
No app switching. Mid-range system requirements. MVP complete.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import requests
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import os

# M5 Attestation
try:
    from lantern_capability_attestation import CapabilityAttestation
    M5_AVAILABLE = True
except ImportError:
    M5_AVAILABLE = False

# Audio
try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# RetroArch
RETROARCH_PATH = Path("D:\\Games\\RetroarchWin\\retroarch.exe")
RETROARCH_AVAILABLE = RETROARCH_PATH.exists()


class LanternIntegrated:
    """Unified Lantern platform: Chat, Music, Games, Browser, Email, Videos, Reminders."""

    def __init__(self, root, selected_provider: str = "ollama"):
        self.root = root
        self.selected_provider = selected_provider
        self.root.title("Lantern OS")
        self.root.geometry("1200x800")

        # Config
        self.config = self._load_config()
        self.current_model = self.config["llm_providers"][selected_provider]["config"].get("model", "local")

        # Font prefs
        self.font_size = self._load_font_size()
        self.font_family = self._load_font_family()

        # M5 Attestation
        self.attestation = None
        if M5_AVAILABLE:
            try:
                self.attestation = CapabilityAttestation()
                providers_config = self._extract_provider_configs()
                self.attestation.start_continuous_attestation(providers_config)
            except Exception as e:
                print(f"[M5] Warning: {e}")

        # Build unified UI
        self._build_ui()
        self.message_count = 0
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _load_config(self):
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            return json.load(f)

    def _load_font_size(self) -> int:
        try:
            prefs_path = Path.home() / ".lantern" / "user-prefs.json"
            if prefs_path.exists():
                with open(prefs_path) as f:
                    return json.load(f).get("font_size", 10)
        except:
            pass
        return 10

    def _load_font_family(self) -> str:
        try:
            prefs_path = Path.home() / ".lantern" / "user-prefs.json"
            if prefs_path.exists():
                with open(prefs_path) as f:
                    return json.load(f).get("font_family", "Consolas")
        except:
            pass
        return "Consolas"

    def _extract_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        providers = {}
        try:
            for provider_name, provider_cfg in self.config.get("llm_providers", {}).items():
                providers[provider_name] = provider_cfg
        except Exception as e:
            print(f"[M5] Warning: {e}")
        return providers

    def _build_ui(self):
        """Build unified dashboard with 7 tabs."""
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(header, text="Lantern OS", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text=f"Model: {self.current_model}", font=("Segoe UI", 9), foreground="gray").pack(side=tk.RIGHT)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Chat
        chat_tab = ttk.Frame(self.notebook)
        self.notebook.add(chat_tab, text="💬 Chat")
        self._build_chat_tab(chat_tab)

        # Tab 2: Music
        music_tab = ttk.Frame(self.notebook)
        self.notebook.add(music_tab, text="🎵 Music")
        self._build_music_tab(music_tab)

        # Tab 3: Games (RetroArch)
        games_tab = ttk.Frame(self.notebook)
        self.notebook.add(games_tab, text="🎮 Games")
        self._build_games_tab(games_tab)

        # Tab 4: Browser
        browser_tab = ttk.Frame(self.notebook)
        self.notebook.add(browser_tab, text="🌐 Browser")
        self._build_browser_tab(browser_tab)

        # Tab 5: Videos
        videos_tab = ttk.Frame(self.notebook)
        self.notebook.add(videos_tab, text="📹 Videos")
        self._build_videos_tab(videos_tab)

        # Tab 6: Email
        email_tab = ttk.Frame(self.notebook)
        self.notebook.add(email_tab, text="📧 Email")
        self._build_email_tab(email_tab)

        # Tab 7: Reminders
        reminders_tab = ttk.Frame(self.notebook)
        self.notebook.add(reminders_tab, text="📋 Reminders")
        self._build_reminders_tab(reminders_tab)

        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=2)
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, font=("Segoe UI", 8))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.capability_label = ttk.Label(status_frame, text="● Operational", font=("Segoe UI", 8))
        self.capability_label.pack(side=tk.RIGHT, padx=(10, 0))

    def _build_chat_tab(self, parent):
        """Chat with LLM."""
        header = ttk.Label(parent, text="Chat", font=("Segoe UI", 12, "bold"))
        header.pack(padx=10, pady=5)

        display_frame = ttk.Frame(parent)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(display_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_display = tk.Text(display_frame, yscrollcommand=scrollbar.set,
                                    font=(self.font_family, self.font_size),
                                    bg="#1e1e1e", fg="#e0e0e0", wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.chat_display.yview)

        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.input_field = tk.Text(input_frame, height=3, font=(self.font_family, self.font_size),
                                   bg="#2d2d2d", fg="#e0e0e0")
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_field.bind("<Control-Return>", lambda e: self.send_message())

        send_btn = tk.Button(input_frame, text="Send", command=self.send_message,
                            bg="#1e1e1e", fg="#00ff88", font=("Segoe UI", 10, "bold"))
        send_btn.pack(side=tk.LEFT)

        self._display_message("Lantern", f"Connected to {self.current_model}")
        if M5_AVAILABLE:
            self._display_message("System", "M5 Attestation active")

    def _display_message(self, sender: str, text: str):
        """Display chat message."""
        self.chat_display.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{ts}] {sender}: {text}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def send_message(self):
        """Send message to LLM."""
        user_input = self.input_field.get("1.0", tk.END).strip()
        if not user_input:
            return

        self.input_field.delete("1.0", tk.END)
        self._display_message("You", user_input)
        self.status_label.config(text="Thinking...")
        self.message_count += 1

        thread = threading.Thread(target=self._get_llm_response, args=(user_input,), daemon=True)
        thread.start()

    def _get_llm_response(self, prompt: str):
        """Get response from LLM."""
        try:
            endpoint = self.config["llm_providers"][self.selected_provider]["endpoint"]
            payload = {
                "model": self.current_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 256
            }
            response = requests.post(endpoint, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if "choices" in data:
                    content = data["choices"][0].get("message", {}).get("content", "No response")
                    self._display_message("Lantern", content)
                    self.status_label.config(text=f"Ready ({self.message_count} messages)")
                else:
                    self._display_message("Error", "Invalid response format")
            else:
                self._display_message("Error", f"HTTP {response.status_code}")
        except Exception as e:
            self._display_message("Error", str(e)[:100])

    def _build_music_tab(self, parent):
        """Curated soundscape player."""
        header = ttk.Label(parent, text="Curated Soundscape", font=("Segoe UI", 12, "bold"))
        header.pack(padx=10, pady=5)

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sound_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        font=(self.font_family, 10), bg="#2d2d2d", fg="#e0e0e0")
        self.sound_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sound_listbox.yview)
        self._load_sound_library()

        controls = ttk.Frame(parent)
        controls.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(controls, text="▶ Play", command=self._play_sound,
                 bg="#1e1e1e", fg="#00ff88", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="⏹ Stop", command=self._stop_sound,
                 bg="#1e1e1e", fg="#ff6b6b", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        self.music_status = ttk.Label(parent, text="Ready", font=("Segoe UI", 9))
        self.music_status.pack(padx=10)

    def _load_sound_library(self):
        """Load sounds from ~/.lantern/sounds/."""
        sounds_dir = Path.home() / ".lantern" / "sounds"
        self.sound_files = {}
        if sounds_dir.exists():
            for f in sorted(sounds_dir.glob("*.ogg")) + sorted(sounds_dir.glob("*.wav")):
                name = f.stem.replace("_", " ").title()
                self.sound_listbox.insert(tk.END, name)
                self.sound_files[name] = str(f)

    def _play_sound(self):
        """Play selected sound."""
        sel = self.sound_listbox.curselection()
        if not sel or not AUDIO_AVAILABLE:
            self.music_status.config(text="Select a sound")
            return
        name = self.sound_listbox.get(sel[0])
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.sound_files[name])
            pygame.mixer.music.play()
            self.music_status.config(text=f"Playing: {name}", foreground="#00ff88")
        except Exception as e:
            self.music_status.config(text=str(e)[:40], foreground="#ff6b6b")

    def _stop_sound(self):
        """Stop playback."""
        if AUDIO_AVAILABLE:
            pygame.mixer.music.stop()
            self.music_status.config(text="Stopped")

    def _build_games_tab(self, parent):
        """RetroArch gaming."""
        if not RETROARCH_AVAILABLE:
            ttk.Label(parent, text="RetroArch not found at D:\\Games\\RetroarchWin\\",
                     font=("Segoe UI", 11), foreground="red").pack(pady=20)
            return

        header = ttk.Label(parent, text="Games (RetroArch)", font=("Segoe UI", 12, "bold"))
        header.pack(padx=10, pady=5)

        info = ttk.Label(parent, text="Multi-system retro gaming emulator",
                        font=("Segoe UI", 9), foreground="gray")
        info.pack(padx=10)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="🎮 Launch RetroArch", command=self._launch_retroarch,
                 bg="#1e1e1e", fg="#00ff88", font=("Segoe UI", 10, "bold"),
                 width=30, height=2).pack(pady=10)

        self.games_status = ttk.Label(parent, text="Ready to launch", font=("Segoe UI", 9))
        self.games_status.pack(padx=10)

    def _launch_retroarch(self):
        """Launch RetroArch."""
        try:
            subprocess.Popen(str(RETROARCH_PATH))
            self.games_status.config(text="RetroArch launched ✓", foreground="#00ff88")
        except Exception as e:
            self.games_status.config(text=f"Error: {str(e)[:40]}", foreground="#ff6b6b")

    def _build_browser_tab(self, parent):
        """Web browser."""
        header = ttk.Label(parent, text="Browser", font=("Segoe UI", 12, "bold"))
        header.pack(padx=10, pady=5)

        url_frame = ttk.Frame(parent)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        self.url_input = ttk.Entry(url_frame)
        self.url_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.url_input.insert(0, "https://")

        tk.Button(url_frame, text="Open", command=self._open_browser,
                 bg="#1e1e1e", fg="#00ff88", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        self.browser_status = ttk.Label(parent, text="Enter URL and click Open", font=("Segoe UI", 9))
        self.browser_status.pack(padx=10, pady=20)

    def _open_browser(self):
        """Open URL in default browser."""
        url = self.url_input.get()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            self.browser_status.config(text=f"Opening {url}...", foreground="#00ff88")
        except Exception as e:
            self.browser_status.config(text=f"Error: {str(e)[:40]}", foreground="#ff6b6b")

    def _build_videos_tab(self, parent):
        """Video player placeholder."""
        header = ttk.Label(parent, text="Videos", font=("Segoe UI", 12, "bold"))
        header.pack(padx=10, pady=5)

        info = ttk.Label(parent, text="Video directory: ~/.lantern/videos/\n\nSupported: MP4, WebM, MKV",
                        font=("Segoe UI", 10), foreground="gray")
        info.pack(padx=10, pady=20)

        video_dir = Path.home() / ".lantern" / "videos"
        if video_dir.exists():
            videos = list(video_dir.glob("*.[Mm][Pp]4")) + list(video_dir.glob("*.[Mm][Kk][Vv]"))
            if videos:
                ttk.Label(parent, text=f"Found {len(videos)} videos", font=("Segoe UI", 9)).pack()

    def _build_email_tab(self, parent):
        """Email client placeholder."""
        header = ttk.Label(parent, text="Email", font=("Segoe UI", 12, "bold"))
        header.pack(padx=10, pady=5)

        config_frame = ttk.LabelFrame(parent, text="Email Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(config_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(config_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, width=30, show="*").grid(row=1, column=1, padx=5, pady=5)

        tk.Button(config_frame, text="Connect", bg="#1e1e1e", fg="#00ff88",
                 font=("Segoe UI", 10, "bold")).grid(row=2, column=1, sticky=tk.E, padx=5, pady=10)

    def _build_reminders_tab(self, parent):
        """Reminders/calendar."""
        header = ttk.Label(parent, text="Reminders", font=("Segoe UI", 12, "bold"))
        header.pack(padx=10, pady=5)

        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(frame, text="Reminder:", font=("Segoe UI", 9)).pack(anchor=tk.W)
        reminder_input = tk.Text(frame, height=3, font=(self.font_family, 10),
                                bg="#2d2d2d", fg="#e0e0e0")
        reminder_input.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Date:", font=("Segoe UI", 9)).pack(anchor=tk.W)
        ttk.Entry(frame).pack(fill=tk.X, pady=5)

        tk.Button(frame, text="Set Reminder", bg="#1e1e1e", fg="#00ff88",
                 font=("Segoe UI", 10, "bold")).pack(pady=10)

        reminders_list = tk.Listbox(frame, font=(self.font_family, 9),
                                    bg="#2d2d2d", fg="#e0e0e0", height=8)
        reminders_list.pack(fill=tk.BOTH, expand=True, pady=10)
        reminders_list.insert(tk.END, "No reminders set")

    def _on_window_close(self):
        """Clean shutdown."""
        if self.attestation:
            self.attestation.stop_continuous_attestation()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LanternIntegrated(root)
    root.mainloop()

    # Tab 8: Master Plan (NEW - Added for Frank Sinatra narration)
    def _add_master_plan_tab(self):
        """Add Master Plan tab with Frank Sinatra narration."""
        master_plan_tab = ttk.Frame(self.notebook)
        self.notebook.add(master_plan_tab, text="📖 Master Plan")
        
        # Controls
        controls = ttk.Frame(master_plan_tab)
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(controls, text="▶ Play Narration (Frank Sinatra Voice)", 
                   command=self._play_master_plan_narration).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="🖨 Print Master Plan", 
                   command=self._print_master_plan).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="⏸ Pause", 
                   command=self._pause_narration).pack(side=tk.LEFT, padx=5)
        
        # Display area
        display = ttk.Frame(master_plan_tab)
        display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.master_plan_text = scrolledtext.ScrolledText(
            display, height=30, width=100, 
            font=(self.font_family, self.font_size),
            wrap=tk.WORD
        )
        self.master_plan_text.pack(fill=tk.BOTH, expand=True)
        
        # Load and display master plan
        self._load_master_plan_display()
    
    def _load_master_plan_display(self):
        """Load master plan text for display."""
        try:
            narrator_dir = Path.home() / '.lantern' / 'narration'
            plan_file = narrator_dir / 'master-plan-print.txt'
            
            if plan_file.exists():
                with open(plan_file, 'r') as f:
                    self.master_plan_text.insert(tk.END, f.read())
            else:
                self.master_plan_text.insert(tk.END, 
                    "[Master Plan not yet generated]\n\n"
                    "Click 'Play Narration' to generate the Frank Sinatra narration.")
        except Exception as e:
            self.master_plan_text.insert(tk.END, f"Error loading master plan: {e}")
    
    def _play_master_plan_narration(self):
        """Play master plan with Frank Sinatra voice narration."""
        try:
            # Import narrator
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from master_plan_narrator import MasterPlanNarrator
            
            narrator = MasterPlanNarrator()
            result = narrator.render_master_plan_all_channels()
            
            # Show success
            messagebox.showinfo("Master Plan", 
                f"Master plan narration generated!\n\n"
                f"Files: {len(result.get('files_generated', []))} generated\n"
                f"Duration: {result['narration_metadata'].get('estimated_duration_minutes')} minutes\n"
                f"\nFrank Sinatra voice narration is ready for playback.")
            
            # Reload display
            self._load_master_plan_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate narration: {e}")
    
    def _print_master_plan(self):
        """Print master plan to file."""
        try:
            narrator_dir = Path.home() / '.lantern' / 'narration'
            plan_file = narrator_dir / 'master-plan-print.txt'
            
            if plan_file.exists():
                import webbrowser
                webbrowser.open(str(plan_file))
                messagebox.showinfo("Print", f"Master plan printed to:\n{plan_file}")
            else:
                messagebox.showwarning("Not Found", "Master plan not yet generated. Click 'Play Narration' first.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not print: {e}")
    
    def _pause_narration(self):
        """Pause narration (placeholder for audio playback control)."""
        messagebox.showinfo("Playback", "Narration paused. Click 'Play' to resume.")
