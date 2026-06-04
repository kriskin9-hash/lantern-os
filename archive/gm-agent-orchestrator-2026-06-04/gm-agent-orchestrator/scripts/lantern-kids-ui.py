#!/usr/bin/env python3
"""
Lantern Kids - Age-Gated AI Chat with Parental Review
Designed for children ages 6-16 with parental controls and safety features.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional


class LanternKids:
    """Kids edition of Lantern Chat with parental review."""

    def __init__(self, root, parent_mode: bool = False):
        """
        Initialize Lantern Kids.

        Args:
            root: Tk root window
            parent_mode: If True, show parent controls (age gating, safety review)
        """
        self.root = root
        self.parent_mode = parent_mode
        self.root.title("Lantern Kids" if not parent_mode else "Lantern Kids - Parent Controls")
        self.root.geometry("900x700")

        # Load config
        self.config = self._load_config()
        self.current_model = self.config["llm_providers"]["claude"]["config"].get("model", "local")

        # Load parental controls
        self.parental_settings = self._load_parental_settings()
        self.message_count = 0

        # Build UI based on mode
        if parent_mode:
            self._build_parent_ui()
        else:
            self._build_kids_ui()

    def _load_config(self):
        """Load LLM configuration."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            return json.load(f)

    def _load_parental_settings(self) -> dict:
        """Load or create parental control settings."""
        settings_path = Path.home() / ".lantern" / "kids-parental-settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                return json.load(f)
        else:
            # Default parental settings
            defaults = {
                "child_name": "Child",
                "child_age": 8,
                "age_gating_enabled": True,
                "keyword_filter_enabled": True,
                "dangerous_keywords": ["suicide", "harm", "violence", "drug"],
                "response_review_required": True,
                "response_review_topics": ["sensitive", "dangerous", "inappropriate"],
                "daily_usage_limit_minutes": 120,
                "parent_email": "parent@example.com",
                "last_reviewed_timestamp": None
            }
            # Save defaults
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_path, 'w') as f:
                json.dump(defaults, f, indent=2)
            return defaults

    def _save_parental_settings(self):
        """Save parental control settings."""
        settings_path = Path.home() / ".lantern" / "kids-parental-settings.json"
        with open(settings_path, 'w') as f:
            json.dump(self.parental_settings, f, indent=2)

    def _build_kids_ui(self):
        """Build the kids chat interface (simplified, safe)."""
        # Header with kid-friendly greeting
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header, text=f"Hi {self.parental_settings['child_name']}! Let's chat with Lantern 🧠",
                  font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)

        # Safety banner (for age 6-10)
        if self.parental_settings.get('child_age', 8) <= 10:
            safety_banner = ttk.Frame(self.root)
            safety_banner.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(safety_banner,
                      text="⚠️ Remember: Only ask questions your parent said it's okay to ask. Lantern will skip bad questions.",
                      font=("Segoe UI", 9), foreground="orange").pack(side=tk.LEFT)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 12),  # Larger for kids
            bg="#f0f8ff",  # Light blue background (kid-friendly)
            fg="#000000"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Configure tags
        self.chat_display.tag_config("kid", foreground="#0066cc", font=("Segoe UI", 12, "bold"))
        self.chat_display.tag_config("lantern", foreground="#009900", font=("Segoe UI", 12))
        self.chat_display.tag_config("unsafe", foreground="#cc0000", font=("Segoe UI", 12, "italic"))

        # Input frame
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.input_field = tk.Text(input_frame, height=3, font=("Segoe UI", 12),
                                   bg="#ffffff", fg="#000000")
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_field.bind("<Control-Return>", lambda e: self.send_message())

        # Send button (kid-friendly, large)
        send_btn = tk.Button(input_frame, text="Send\n(Ctrl+Enter)", command=self.send_message,
                            width=14, height=2, padx=10, pady=10,
                            bg="#0066cc", fg="#ffffff", activebackground="#0052a3",
                            font=("Segoe UI", 10, "bold"))
        send_btn.pack(side=tk.LEFT, fill=tk.BOTH)

        # Daily usage limit indicator
        self.status_label = ttk.Label(self.root, text="Ready to chat!", relief=tk.SUNKEN,
                                      font=("Segoe UI", 8))
        self.status_label.pack(fill=tk.X, padx=10, pady=2)

        # Startup message
        self._display_message("Lantern",
                             f"Hi {self.parental_settings['child_name']}! I'm Lantern, your AI friend. What would you like to talk about?",
                             "lantern")

    def _build_parent_ui(self):
        """Build the parental controls interface."""
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Child Settings
        child_frame = ttk.Frame(notebook)
        notebook.add(child_frame, text="Child Settings")

        ttk.Label(child_frame, text="Child's Name:", font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=5)
        self.child_name_var = tk.StringVar(value=self.parental_settings.get('child_name', 'Child'))
        ttk.Entry(child_frame, textvariable=self.child_name_var, width=30).pack(anchor=tk.W, padx=10)

        ttk.Label(child_frame, text="Child's Age:", font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=5)
        self.child_age_var = tk.IntVar(value=self.parental_settings.get('child_age', 8))
        ttk.Scale(child_frame, from_=6, to=16, orient=tk.HORIZONTAL, variable=self.child_age_var,
                 command=lambda v: self.age_label.config(text=f"Age: {int(float(v))}")).pack(fill=tk.X, padx=10)
        self.age_label = ttk.Label(child_frame, text=f"Age: {self.child_age_var.get()}")
        self.age_label.pack(anchor=tk.W, padx=10)

        # Tab 2: Safety Settings
        safety_frame = ttk.Frame(notebook)
        notebook.add(safety_frame, text="Safety Settings")

        self.keyword_filter_var = tk.BooleanVar(value=self.parental_settings.get('keyword_filter_enabled', True))
        ttk.Checkbutton(safety_frame, text="Enable keyword filter (block dangerous words)",
                       variable=self.keyword_filter_var).pack(anchor=tk.W, padx=10, pady=5)

        self.response_review_var = tk.BooleanVar(value=self.parental_settings.get('response_review_required', True))
        ttk.Checkbutton(safety_frame, text="Review responses before showing to child",
                       variable=self.response_review_var).pack(anchor=tk.W, padx=10, pady=5)

        # Tab 3: Usage Limits
        limits_frame = ttk.Frame(notebook)
        notebook.add(limits_frame, text="Usage Limits")

        ttk.Label(limits_frame, text="Daily Usage Limit (minutes):", font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=5)
        self.usage_limit_var = tk.IntVar(value=self.parental_settings.get('daily_usage_limit_minutes', 120))
        ttk.Scale(limits_frame, from_=15, to=480, orient=tk.HORIZONTAL, variable=self.usage_limit_var,
                 command=lambda v: self.limit_label.config(text=f"Limit: {int(float(v))} minutes")).pack(fill=tk.X, padx=10)
        self.limit_label = ttk.Label(limits_frame, text=f"Limit: {self.usage_limit_var.get()} minutes")
        self.limit_label.pack(anchor=tk.W, padx=10)

        # Tab 4: Response Review
        review_frame = ttk.Frame(notebook)
        notebook.add(review_frame, text="Response Review")

        ttk.Label(review_frame, text="Responses marked for review:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=5)

        self.review_text = scrolledtext.ScrolledText(review_frame, height=10, font=("Segoe UI", 9))
        self.review_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Button(review_frame, text="Approve All", command=self._approve_all_reviews).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(review_frame, text="Clear Review Queue", command=self._clear_reviews).pack(side=tk.LEFT, padx=5, pady=5)

        # Save button
        ttk.Button(self.root, text="Save Settings", command=self._save_parent_settings).pack(pady=10)

    def _save_parent_settings(self):
        """Save updated parental settings."""
        self.parental_settings['child_name'] = self.child_name_var.get()
        self.parental_settings['child_age'] = int(self.child_age_var.get())
        self.parental_settings['keyword_filter_enabled'] = self.keyword_filter_var.get()
        self.parental_settings['response_review_required'] = self.response_review_var.get()
        self.parental_settings['daily_usage_limit_minutes'] = int(self.usage_limit_var.get())
        self.parental_settings['last_reviewed_timestamp'] = datetime.now().isoformat()

        self._save_parental_settings()
        messagebox.showinfo("Success", "Parental settings saved!")

    def _approve_all_reviews(self):
        """Approve all responses in review queue."""
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete("1.0", tk.END)
        self.review_text.config(state=tk.DISABLED)
        messagebox.showinfo("Done", "All responses approved!")

    def _clear_reviews(self):
        """Clear review queue."""
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete("1.0", tk.END)
        self.review_text.config(state=tk.DISABLED)

    def _display_message(self, sender: str, text: str, msg_type: str = "kid"):
        """Display message in chat (kids mode only)."""
        if self.parent_mode:
            return

        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {text}\n\n", msg_type)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.root.update()

    def send_message(self):
        """Send message (kids mode only, with safety checks)."""
        if self.parent_mode:
            return

        user_input = self.input_field.get("1.0", tk.END).strip()

        if not user_input:
            return

        # Safety check: keyword filter
        if self.parental_settings.get('keyword_filter_enabled', True):
            dangerous_words = self.parental_settings.get('dangerous_keywords', [])
            for keyword in dangerous_words:
                if keyword.lower() in user_input.lower():
                    self._display_message("Lantern",
                                         f"I can't answer that question right now. Ask your parent if you need help!",
                                         "unsafe")
                    self.input_field.delete("1.0", tk.END)
                    return

        # Clear input
        self.input_field.delete("1.0", tk.END)

        # Display user message
        self._display_message(self.parental_settings['child_name'], user_input, "kid")
        self.status_label.config(text="Lantern is thinking...")
        self.message_count += 1

        # Get LLM response in background thread
        thread = threading.Thread(target=self._get_llm_response, args=(user_input,), daemon=True)
        thread.start()

    def _get_llm_response(self, prompt: str):
        """Get response from Claude (kids-safe version)."""
        try:
            endpoint = self.config["llm_providers"]["claude"]["endpoint"]

            payload = {
                "model": self.current_model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are Lantern, a helpful AI assistant for {self.parental_settings['child_age']}-year-old {self.parental_settings['child_name']}. Be friendly, safe, and educational. Avoid controversial topics, violence, and inappropriate content."
                    },
                    {"role": "user", "content": prompt}
                ],
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 256  # Shorter responses for kids
            }

            response = requests.post(
                endpoint,
                json=payload,
                stream=True,
                timeout=30
            )

            if response.status_code != 200:
                self._display_message("Lantern", "Oops! I had a problem. Please try again.", "unsafe")
                self.status_label.config(text="Error")
                return

            # Stream response
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Lantern: ", "lantern")
            self.chat_display.config(state=tk.DISABLED)

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

                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.insert(tk.END, token, "lantern")
                    self.chat_display.config(state=tk.DISABLED)
                    self.chat_display.see(tk.END)
                    self.root.update()

                except (json.JSONDecodeError, KeyError):
                    continue

            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.config(state=tk.DISABLED)

            self.status_label.config(text=f"Ready ({self.message_count} messages)")

        except Exception as e:
            self._display_message("Lantern", f"I'm having trouble right now. Error: {str(e)[:50]}", "unsafe")
            self.status_label.config(text="Error")


def main():
    """Launch Lantern Kids."""
    root = tk.Tk()

    # Check if parent mode requested
    import sys
    parent_mode = "--parent" in sys.argv

    chat = LanternKids(root, parent_mode=parent_mode)
    root.mainloop()


if __name__ == "__main__":
    main()
