#!/usr/bin/env python3
"""Operator-first Lantern desktop chat app.

GPT-style local chat for Alex/operator, Lantern, and the HFF repo.
The default surface is not a child/protected-play UI.
"""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SCRIPT = REPO_ROOT / "apps" / "lantern-local-chat" / "local_lantern_server.py"
DEFAULT_PORT = 8765
MAX_PORT = 8799
INTERNAL_BACKEND_MODE = "engineer"
GOAL_POSTS = (
    "Alex/operator-first. Local-first. Show state. Say the limit. "
    "Lantern chooses the best fit inside the goal posts. No child default. "
    "No hidden autonomy. Camera use requires separate explicit local approval. Time is visible."
)

PALETTE = {
    "bg": "#0f172a", "panel": "#111827", "surface": "#020617", "input": "#0b1220",
    "text": "#e5e7eb", "muted": "#94a3b8", "accent": "#38bdf8",
    "operator": "#a7f3d0", "lantern": "#fef3c7",
}


class LocalLantern:
    def __init__(self, preferred_port: int = DEFAULT_PORT, max_port: int = MAX_PORT) -> None:
        self.preferred_port = preferred_port
        self.max_port = max_port
        self.endpoint: str | None = None
        self.process: subprocess.Popen[str] | None = None

    @staticmethod
    def endpoint_for(port: int) -> str:
        return f"http://127.0.0.1:{port}"

    @staticmethod
    def can_bind(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

    def health(self, endpoint: str | None = None) -> dict[str, Any]:
        target = endpoint or self.endpoint or self.endpoint_for(self.preferred_port)
        url = target.rstrip("/") + "/healthz"
        try:
            with urlopen(Request(url, headers={"accept": "application/json"}), timeout=1.0) as response:  # noqa: S310
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return {"ok": False, "url": url, "error": f"HTTP {exc.code}"}
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return {"ok": False, "url": url, "error": type(exc).__name__}
        return data if isinstance(data, dict) else {"ok": False, "url": url, "error": "invalid response"}

    def find_running_endpoint(self) -> str | None:
        for port in [self.preferred_port, *range(DEFAULT_PORT, self.max_port + 1)]:
            endpoint = self.endpoint_for(port)
            if self.health(endpoint).get("ok") is True:
                return endpoint
        return None

    def choose_free_endpoint(self) -> str:
        for port in [self.preferred_port, *range(DEFAULT_PORT, self.max_port + 1)]:
            if self.can_bind(port):
                return self.endpoint_for(port)
        return self.endpoint_for(self.preferred_port)

    def ensure_backend(self) -> str:
        running = self.find_running_endpoint()
        if running:
            self.endpoint = running
            return running
        endpoint = self.choose_free_endpoint()
        port = int(endpoint.rsplit(":", 1)[1])
        spawn_env = dict(os.environ)
        config_path = Path.home() / ".lantern" / "config.json"
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                sub_env = cfg.get("substrate_env") if isinstance(cfg, dict) else None
                if isinstance(sub_env, dict):
                    spawn_env.update({k: v for k, v in sub_env.items() if isinstance(k, str) and isinstance(v, str)})
            except (OSError, json.JSONDecodeError):
                pass
        self.process = subprocess.Popen(
            [sys.executable, str(BACKEND_SCRIPT), "--host", "127.0.0.1", "--port", str(port)],
            cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            text=True, env=spawn_env, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if self.health(endpoint).get("ok") is True:
                self.endpoint = endpoint
                return endpoint
            time.sleep(0.25)
        raise RuntimeError(f"Lantern backend did not become reachable at {endpoint}")

    def chat(self, message: str) -> dict[str, Any]:
        if not self.endpoint:
            self.ensure_backend()
        url = (self.endpoint or self.endpoint_for(self.preferred_port)).rstrip("/") + "/chat"
        payload = json.dumps({"message": message, "mode": INTERNAL_BACKEND_MODE}).encode("utf-8")
        request = Request(url, data=payload, headers={"content-type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=25.0) as response:  # noqa: S310
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return {"ok": False, "answer": f"Local Lantern backend is not reachable: {type(exc).__name__}"}
        return data if isinstance(data, dict) else {"ok": False, "answer": "Lantern returned a non-object response."}

    def stop_owned_backend(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.process = None


def plain_chat_answer(data: dict[str, Any]) -> str:
    if data.get("ok") is not True:
        return str(data.get("answer") or data.get("error") or "Lantern could not answer.")
    if isinstance(data.get("plainAnswer"), str) and data["plainAnswer"].strip():
        return data["plainAnswer"].strip()
    answer = str(data.get("answer") or "Lantern local answer was empty.")
    kept: list[str] = []
    for line in answer.splitlines():
        if line.strip().startswith(("Sources:", "Limits:", "Minimal convergence frame:")):
            break
        if not line.startswith("Lantern local answer"):
            kept.append(line)
    return "\n".join(kept).strip() or answer


class OperatorLanternChat(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lantern — Operator Chat")
        self.geometry("1120x780")
        self.minsize(860, 600)
        self.configure(bg=PALETTE["bg"])
        self.client = LocalLantern()
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.status = tk.StringVar(value="Starting local Lantern…")
        self.endpoint_text = tk.StringVar(value="Backend: connecting")
        self.time_text = tk.StringVar(value="Time: —")
        self.waiting_for_reply = False
        self.send_button: ttk.Button | None = None
        self._theme()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(100, self._poll)
        self.after(250, self._tick_time)
        threading.Thread(target=self._start_backend, daemon=True).start()

    def _theme(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=PALETTE["bg"])
        style.configure("Panel.TFrame", background=PALETTE["panel"])
        style.configure("TButton", padding=(10, 6))
        style.configure("Accent.TButton", padding=(14, 8))

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=(18, 14, 18, 14))
        outer.pack(fill=tk.BOTH, expand=True)
        header = ttk.Frame(outer)
        header.pack(fill=tk.X)
        tk.Label(header, text="Lantern", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 24, "bold")).pack(side=tk.LEFT)
        right = ttk.Frame(header)
        right.pack(side=tk.RIGHT)
        tk.Label(right, textvariable=self.time_text, bg=PALETTE["bg"], fg=PALETTE["muted"]).pack(anchor="e")
        tk.Label(right, textvariable=self.status, bg=PALETTE["bg"], fg=PALETTE["muted"]).pack(anchor="e")
        tk.Label(right, textvariable=self.endpoint_text, bg=PALETTE["bg"], fg=PALETTE["muted"]).pack(anchor="e")

        panel = ttk.Frame(outer, style="Panel.TFrame", padding=(12, 10, 12, 10))
        panel.pack(fill=tk.X, pady=(14, 10))
        tk.Label(panel, text="Goal posts", bg=PALETTE["panel"], fg=PALETTE["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(panel, text=GOAL_POSTS, bg=PALETTE["panel"], fg=PALETTE["muted"], wraplength=980, justify=tk.LEFT).pack(anchor="w")

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(toolbar, text="Status", command=self.show_status).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Doctor", command=self.ask_doctor).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(toolbar, text="Camera goal post", command=self.camera_note).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(toolbar, text="Clear", command=self.clear).pack(side=tk.LEFT, padx=(8, 0))

        self.output = scrolledtext.ScrolledText(
            outer, wrap=tk.WORD, font=("Segoe UI", 11), background=PALETTE["surface"],
            foreground=PALETTE["text"], insertbackground=PALETTE["text"], relief=tk.FLAT, padx=16, pady=14,
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.tag_configure("system", foreground=PALETTE["muted"])
        self.output.tag_configure("operator", foreground=PALETTE["operator"])
        self.output.tag_configure("lantern", foreground=PALETTE["lantern"])
        self.output.configure(state=tk.DISABLED)

        input_row = ttk.Frame(outer)
        input_row.pack(fill=tk.X, pady=(12, 0))
        self.input = tk.Text(input_row, height=4, wrap=tk.WORD, font=("Segoe UI", 11), background=PALETTE["input"], foreground=PALETTE["text"], insertbackground=PALETTE["text"], relief=tk.FLAT, padx=12, pady=10)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input.bind("<Return>", self._on_enter)
        self.input.bind("<Shift-Return>", self._on_shift_enter)
        self.input.bind("<Control-Return>", self._on_control_enter)
        self.send_button = ttk.Button(input_row, text="Send", style="Accent.TButton", command=self.ask)
        self.send_button.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.input.focus_set()
        self._append_system("Operator Lantern is open. This is the Alex-first surface. Time is visible. Camera is a separate explicit goal post, not a hidden input.")

    def _tick_time(self) -> None:
        self.time_text.set("Time: " + datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))
        self.after(1000, self._tick_time)

    def _start_backend(self) -> None:
        try:
            self.events.put(("backend", self.client.ensure_backend()))
        except Exception as exc:
            self.events.put(("backend_error", str(exc)))

    def _poll(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "backend":
                    self.status.set("Local Lantern ready")
                    self.endpoint_text.set(f"Backend: {payload}")
                elif kind == "backend_error":
                    self.status.set("Backend failed")
                    self.endpoint_text.set("Backend: unavailable")
                    self._append_system(f"Backend failed: {payload}")
                elif kind == "reply":
                    self.waiting_for_reply = False
                    if self.send_button:
                        self.send_button.configure(state=tk.NORMAL)
                    self._append_lantern(str(payload))
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def ask(self) -> None:
        message = self.input.get("1.0", tk.END).strip()
        if not message or self.waiting_for_reply:
            return
        self.input.delete("1.0", tk.END)
        self._append_operator(message)
        self.waiting_for_reply = True
        if self.send_button:
            self.send_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._ask_worker, args=(message,), daemon=True).start()

    def ask_doctor(self) -> None:
        self.input.delete("1.0", tk.END)
        self.input.insert("1.0", "doctor: show local readiness, endpoint, repo state, and next repair step")
        self.ask()

    def _ask_worker(self, message: str) -> None:
        self.events.put(("reply", plain_chat_answer(self.client.chat(message))))

    def show_status(self) -> None:
        messagebox.showinfo("Lantern status", json.dumps(self.client.health(), indent=2))

    def camera_note(self) -> None:
        self._append_system("Camera goal post: allowed only as an explicit local action with visible status. This app does not capture, store, upload, or analyze camera frames by default.")

    def clear(self) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)
        self._append_system("Cleared local display only. Backend state was not modified.")

    def close(self) -> None:
        self.client.stop_owned_backend()
        self.destroy()

    def _on_enter(self, event: tk.Event) -> str:
        self.ask()
        return "break"

    def _on_shift_enter(self, event: tk.Event) -> None:
        return None

    def _on_control_enter(self, event: tk.Event) -> str:
        self.ask()
        return "break"

    def _append(self, who: str, text: str, tag: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, f"{who}\n", tag)
        self.output.insert(tk.END, text.strip() + "\n\n")
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

    def _append_system(self, text: str) -> None:
        self._append("System", text, "system")

    def _append_operator(self, text: str) -> None:
        self._append("Alex", text, "operator")

    def _append_lantern(self, text: str) -> None:
        self._append("Lantern", text, "lantern")


def main() -> None:
    OperatorLanternChat().mainloop()


if __name__ == "__main__":
    main()
