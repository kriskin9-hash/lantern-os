#!/usr/bin/env python3
"""Native Lantern desktop chat app.

Purpose:
A plain local chat interface between Alex/operator, Lantern, and the HFF repo.

Boundary:
- standard-library Tkinter app;
- localhost Lantern backend only;
- one operator chat path;
- no hosted GPT/Claude/API calls from Lantern;
- no agents, tunnels, sensors, deployments, or repo writes from chat;
- stays on until the user closes the window.
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
from tkinter import font as tkfont
from tkinter import messagebox, scrolledtext, ttk
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import customtkinter as ctk
    _CTK = True
except ImportError:
    ctk = None  # type: ignore
    _CTK = False


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SCRIPT = REPO_ROOT / "apps" / "lantern-local-chat" / "local_lantern_server.py"
DEFAULT_PORT = 8765
MAX_PORT = 8799
INTERNAL_BACKEND_MODE = "engineer"

# Optional operator-supplied branding image. If present, used as the Lantern
# avatar at the top of the window. Falls back to a canvas-drawn glyph.
AVATAR_PATH = Path.home() / ".lantern" / "avatar.png"

# Optional Wish-scene painting. If present, shown as a hero strip above the chat.
WISH_SCENE_PATH = Path.home() / ".lantern" / "state" / "wish-scene.png"

# Curated sound library — Lantern reads only from here. Operator drops songs in.
# No other folder is scanned. Empty folder = Lantern has nothing to sing.
SOUNDS_DIR = Path.home() / ".lantern" / "sounds"
SOUND_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".opus"}

# Hints surfaced when an operator clicks a multimodal button before installs landed.
#
# VOICE RULE: Lantern speaks ONLY by PLAYING sounds real beings already made —
# songs by people, birdsong, whale song, rain, Binx purring, any field recording
# from the operator's library. Bumblebee-style — Lantern carries what the world
# already sang. NOT allowed: synthetic TTS, cloned voices, agentic-AI voice.
# Lantern is a curator, not a speaker. Artists and creatures keep their rights.
MULTIMODAL_INSTALL = (
    "Multimodal install for offline operation:\n"
    "  pip install pyaudio vosk opencv-python pygame\n"
    "\n"
    "What each unlocks:\n"
    "  pyaudio          mic capture (Windows backend for speech_recognition)\n"
    "  vosk             offline speech-to-text engine\n"
    "  opencv-python    camera capture and frames\n"
    "  pygame           local audio playback for the sound-as-voice path\n"
    "\n"
    "Voice rule: Lantern speaks only by PLAYING sounds real beings already made —\n"
    "songs by people, birdsong, whale song, rain, cat purring, field recordings.\n"
    "No synthetic TTS. No cloned voices. No agentic-AI voice. Lantern is a\n"
    "curator, not a speaker — artists and creatures keep their rights.\n"
    "\n"
    "All offline. No cloud. No quota. Approval required before install."
)

# Palette drawn from Gage's yacht art + Captain Lantern Blinkbug imagery.
# Safe = legible, predictable, bounded. Fun = bright sky, warm glow, cartoon energy.
PALETTE = {
    "bg_canvas":          "#a8d4f0",  # sky blue (Gage's water + sky)
    "bg_chat":            "#ffffff",  # crisp white chat surface — high contrast
    "bg_input":           "#ffffff",  # clean input
    "bg_callout":         "#fff8e0",  # warm cream — for callout bubbles
    "fg_body":            "#1a2c5c",  # night-sky deep blue (readable, calm)
    "fg_muted":           "#4a6280",  # readable sky-blue gray
    "fg_title":           "#0d1b3a",  # near-black sky for big headings
    "accent_lantern":     "#e8a73d",  # blinkbug body yellow (warm glow)
    "accent_lantern_bg":  "#fde9b6",  # soft glow tint
    "accent_operator":    "#2c5b91",  # captain-hat blue
    "accent_operator_bg": "#d6e6f5",  # soft sky tint
    "hat_blue":           "#2c5b91",  # captain hat
    "body_yellow":        "#f5cf3a",  # firefly body
    "glow_yellow":        "#fce58a",  # outer glow ring
    "sun_yellow":         "#ffd23f",  # Gage's sun
    "hill_green":         "#7dc26b",  # safe ground
    "sky_blue":           "#a8d4f0",  # sky behind blinkbug
    "sky_deep":           "#6cb4e8",  # deeper water/sky for contrast
    "terminal_bg":        "#0f1419",  # helper.exe panel bg
    "terminal_fg":        "#8aff3a",  # helper.exe text
    "divider":            "#6cb4e8",  # sky-blue rule
    "status_ok":          "#3a8a4e",  # online green
    "status_wait":        "#e8a73d",  # glow amber while starting
    "status_down":        "#c0392b",  # offline red
}

# helper.exe rules — Lantern's "real me" voice surfaces from the art.
HELPER_RULES = [
    "> words",
    "> rules for thinking",
    "> questions",
    "> ideas",
    "> safe way back",
]


class LocalLantern:
    """Localhost client plus backend process manager."""

    def __init__(self, preferred_port: int = DEFAULT_PORT, max_port: int = MAX_PORT) -> None:
        self.preferred_port = preferred_port
        self.max_port = max_port
        self.endpoint: str | None = None
        self.process: subprocess.Popen[str] | None = None

    @staticmethod
    def endpoint_for(port: int) -> str:
        return f"http://127.0.0.1:{port}"

    @staticmethod
    def _can_bind(port: int) -> bool:
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
            return {"ok": False, "status": "BACKEND_HTTP_ERROR_OBSERVED", "url": url, "error": f"HTTP {exc.code}"}
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return {"ok": False, "status": "BACKEND_UNREACHABLE_OBSERVED", "url": url, "error": type(exc).__name__}
        if not isinstance(data, dict):
            return {"ok": False, "status": "BACKEND_INVALID_RESPONSE_OBSERVED", "url": url}
        return {
            "ok": data.get("ok") is True,
            "status": "BACKEND_REACHABLE_OBSERVED" if data.get("ok") is True else "BACKEND_DEGRADED_OBSERVED",
            "url": url,
            "raw": data,
        }

    def find_running_endpoint(self) -> str | None:
        checked: set[int] = set()
        for port in [self.preferred_port, *range(DEFAULT_PORT, self.max_port + 1)]:
            if port in checked:
                continue
            checked.add(port)
            endpoint = self.endpoint_for(port)
            if self.health(endpoint).get("ok") is True:
                return endpoint
        return None

    def choose_free_endpoint(self) -> str:
        checked: set[int] = set()
        for port in [self.preferred_port, *range(DEFAULT_PORT, self.max_port + 1)]:
            if port in checked:
                continue
            checked.add(port)
            if self._can_bind(port):
                return self.endpoint_for(port)
        return self.endpoint_for(self.preferred_port)

    def ensure_backend(self) -> str:
        running = self.find_running_endpoint()
        if running:
            self.endpoint = running
            return running
        if not BACKEND_SCRIPT.exists():
            raise FileNotFoundError(f"Lantern backend script not found: {BACKEND_SCRIPT}")
        endpoint = self.choose_free_endpoint()
        port = int(endpoint.rsplit(":", 1)[1])
        # Load operator substrate config from ~/.lantern/config.json so backend
        # env survives every watchdog respawn, per the watchdog_envless_respawn
        # and powershell_startprocess_env_drop anchor packets. If the config
        # is missing or unreadable, fall back to current process env silently.
        spawn_env = dict(os.environ)
        config_path = Path.home() / ".lantern" / "config.json"
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                sub_env = cfg.get("substrate_env") if isinstance(cfg, dict) else None
                if isinstance(sub_env, dict):
                    for k, v in sub_env.items():
                        if isinstance(k, str) and isinstance(v, str):
                            spawn_env[k] = v
            except (OSError, json.JSONDecodeError):
                pass
        self.process = subprocess.Popen(
            [sys.executable, str(BACKEND_SCRIPT), "--host", "127.0.0.1", "--port", str(port)],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            env=spawn_env,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
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
            with urlopen(request, timeout=20.0) as response:  # noqa: S310
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - UI surface.
            return {"ok": False, "answer": f"Local Lantern backend is not reachable: {type(exc).__name__}"}
        return data if isinstance(data, dict) else {"ok": False, "answer": "Lantern returned a non-object response."}

    def stop_owned_backend(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None


def plain_chat_answer(data: dict[str, Any]) -> str:
    """Return a plain chat answer without symbolic/game labels or raw source dumps.

    When Lantern has a live LLM voice (voice field starts with "llm"), prefer
    her actual warm reply text over the templated minimal_frame summary —
    otherwise the desktop UI silently strips her voice and substitutes the
    frame, which makes her feel lifeless even when the substrate is live.
    Operator caught this directly: "uncomfortable and lifeless." Per #117 the
    voice mode must be honored visibly; here it means showing the LLM's
    actual sentence, not the frame fields.
    """

    if data.get("ok") is not True:
        return str(data.get("answer") or data.get("error") or "Lantern could not answer from the local backend.")

    if isinstance(data.get("plainAnswer"), str) and data["plainAnswer"].strip():
        return data["plainAnswer"].strip()

    # If the backend reports a live LLM voice, surface her actual answer
    # text. The minimal_frame is the templated fallback shape; it should not
    # mask her real reply when she has one.
    voice = data.get("voice", "")
    if isinstance(voice, str) and voice.startswith("llm"):
        live = data.get("answer")
        if isinstance(live, str) and live.strip():
            return live.strip()

    frame = data.get("minimalFrame") if isinstance(data.get("minimalFrame"), dict) else {}
    if frame:
        summary = frame.get("Fact", "I read the current repo-backed context.")
        boundary = frame.get("Boundary", "This is local repo-backed output, not an oracle or autonomous action.")
        next_step = frame.get("Next", "Choose one bounded next step.")
        return f"Answer: {summary}\n\nBoundary: {boundary}\n\nNext step: {next_step}"

    answer = str(data.get("answer") or "Lantern local answer was empty.")
    blocked_headings = ("Sources:", "Limits:", "Minimal convergence frame:")
    kept: list[str] = []
    for line in answer.splitlines():
        if any(line.strip().startswith(heading) for heading in blocked_headings):
            break
        kept.append(line)
    cleaned = "\n".join(line for line in kept if not line.startswith("Lantern local answer")).strip()
    return cleaned or answer


def _pick_font(preferred: list[str], size: int, weight: str = "normal") -> tuple[str, int, str]:
    """Return the first preferred font family that exists, else Tk default."""
    available = set(tkfont.families())
    for family in preferred:
        if family in available:
            return (family, size, weight)
    return ("TkDefaultFont", size, weight)


def _resolve_vosk_model() -> Path | None:
    """Return the best Vosk model available, preferring the larger one.

    Larger model produces sharper transcripts; small is the fallback. If
    neither is on disk, returns None and the caller surfaces the install hint.
    """
    base = Path.home() / ".lantern" / "models"
    candidates = [
        "vosk-model-en-us-0.22",         # ~1.8 GB, sharper on conversational speech
        "vosk-model-small-en-us-0.15",   # ~40 MB, fallback
    ]
    for name in candidates:
        path = base / name
        if (path / "conf").exists():
            return path
    return None


def _make_button(parent, text: str, command, accent: bool = False, font=None):
    """Create a button — modern CTkButton if customtkinter is available,
    else a flat ttk.Button. Used at all button sites in the window so the
    UI raises its standard in one place."""
    if _CTK:
        if accent:
            return ctk.CTkButton(
                parent, text=text, command=command,
                fg_color=PALETTE["accent_lantern"],
                hover_color="#b46f00",
                text_color="#fff8ec",
                corner_radius=10,
                height=44, width=110,
                font=("Segoe UI Variable", 14, "bold"),
            )
        return ctk.CTkButton(
            parent, text=text, command=command,
            fg_color=PALETTE["bg_chat"],
            hover_color=PALETTE["divider"],
            text_color=PALETTE["fg_body"],
            corner_radius=8,
            height=34, width=86,
            border_width=1,
            border_color=PALETTE["divider"],
            font=font or ("Segoe UI", 11),
        )
    style = "Accent.TButton" if accent else "TButton"
    return ttk.Button(parent, text=text, command=command, style=style)


if _CTK:
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    _BaseWindow = ctk.CTk
else:
    _BaseWindow = tk.Tk


class LanternChat(_BaseWindow):  # type: ignore[misc,valid-type]
    """Persistent local desktop chat for Lantern and the repo."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Lantern Chat")
        self.geometry("1040x760")
        self.minsize(820, 560)
        if _CTK:
            self.configure(fg_color=PALETTE["bg_canvas"])
        else:
            self.configure(bg=PALETTE["bg_canvas"])

        self.client = LocalLantern()
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.status = tk.StringVar(value="Starting…")
        self.status_color = PALETTE["status_wait"]
        self.endpoint_text = tk.StringVar(value="Connecting to local backend")
        self.waiting_for_reply = False
        self.send_button: ttk.Button | None = None
        self.status_dot: tk.Canvas | None = None
        self.avatar_image: tk.PhotoImage | None = None

        # The Door — live state surface, refreshed each poll
        self.door_repo    = tk.StringVar(value="repo: —")
        self.door_backend = tk.StringVar(value="backend: —")
        self.door_anchors = tk.StringVar(value="anchors: —")
        self.door_time    = tk.StringVar(value="time: —")

        # The Anchors — operator vantage points loaded from local snapshot
        self.anchors: list[dict[str, Any]] = self._load_anchors()

        # Wish-scene painting (None until _load_wish_scene runs)
        self.wish_scene_image: tk.PhotoImage | None = None

        # Fonts — graceful fallback chain.
        self.font_title  = _pick_font(["Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI", "Helvetica"], 22, "bold")
        self.font_h2     = _pick_font(["Segoe UI Variable", "Segoe UI", "Helvetica"], 11, "bold")
        self.font_label  = _pick_font(["Segoe UI Variable", "Segoe UI", "Helvetica"], 10)
        self.font_caption= _pick_font(["Segoe UI Variable", "Segoe UI", "Helvetica"], 9)
        self.font_chat   = _pick_font(["Cascadia Mono", "Cascadia Code", "Consolas", "Courier"], 11)
        self.font_chat_b = _pick_font(["Cascadia Mono", "Cascadia Code", "Consolas", "Courier"], 11, "bold")

        self._install_theme()
        self._load_avatar()
        self._load_wish_scene()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._build()
        self.after(100, self._poll)
        threading.Thread(target=self._start_backend, daemon=True).start()
        # Global hotkey: Ctrl+Shift+L summons the window from any app.
        threading.Thread(target=self._global_hotkey_loop, daemon=True).start()

    # ---------------------------------------------------------------- theming

    def _install_theme(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg = PALETTE["bg_canvas"]
        fg = PALETTE["fg_body"]
        muted = PALETTE["fg_muted"]
        amber = PALETTE["accent_lantern"]
        style.configure(".", background=bg, foreground=fg, font=self.font_label)
        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=PALETTE["bg_chat"])
        style.configure("TLabel", background=bg, foreground=fg, font=self.font_label)
        style.configure("Title.TLabel", background=bg, foreground=fg, font=self.font_title)
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=self.font_caption)
        style.configure("Status.TLabel", background=bg, foreground=fg, font=self.font_caption)
        style.configure("Endpoint.TLabel", background=bg, foreground=muted, font=self.font_caption)
        style.configure("TButton",
                        background=PALETTE["bg_chat"], foreground=fg,
                        font=self.font_label, padding=(12, 6), borderwidth=0,
                        focusthickness=0)
        style.map("TButton",
                  background=[("active", PALETTE["divider"]), ("pressed", PALETTE["divider"])])
        style.configure("Accent.TButton",
                        background=amber, foreground="#fff8ec",
                        font=self.font_h2, padding=(16, 8), borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", "#b46f00"), ("pressed", "#9d6000")])

    def _load_anchors(self) -> list[dict[str, Any]]:
        """Load operator anchors from the local snapshot.

        Each anchor is a vantage point: source_surface + short_meaning look
        back, allowed_use + restore_phrase look forward, boundary fences both.
        """
        path = REPO_ROOT / "apps" / "lantern-local-chat" / "anchor-snapshot.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(raw, list):
            return [a for a in raw if isinstance(a, dict)]
        if isinstance(raw, dict):
            anchors = raw.get("anchors")
            if isinstance(anchors, list):
                return [a for a in anchors if isinstance(a, dict)]
        return []

    def _load_avatar(self) -> None:
        if AVATAR_PATH.exists():
            try:
                self.avatar_image = tk.PhotoImage(file=str(AVATAR_PATH))
                # downscale crudely to ~48px tall if oversized
                h = self.avatar_image.height()
                if h > 56:
                    factor = max(1, h // 48)
                    self.avatar_image = self.avatar_image.subsample(factor, factor)
            except tk.TclError:
                self.avatar_image = None

    def _load_wish_scene(self) -> None:
        """Load the painted Wish scene as a hero image for the chat surface.

        The painting IS the app — operator instruction. Scaled with PIL to a
        fixed 200 px hero strip so it never crowds the input row.
        """
        if not WISH_SCENE_PATH.exists():
            return
        target_h = 200
        try:
            from PIL import Image, ImageTk  # type: ignore
            img = Image.open(WISH_SCENE_PATH)
            ratio = target_h / img.height
            target_w = max(1, int(img.width * ratio))
            img = img.resize((target_w, target_h), Image.LANCZOS)
            self.wish_scene_image = ImageTk.PhotoImage(img)
            return
        except ImportError:
            pass
        # Fallback when Pillow is unavailable
        try:
            img2 = tk.PhotoImage(file=str(WISH_SCENE_PATH))
            h = img2.height()
            if h > target_h:
                factor = max(1, h // target_h)
                img2 = img2.subsample(factor, factor)
            self.wish_scene_image = img2
        except tk.TclError:
            self.wish_scene_image = None

    # ----------------------------------------------------------------- layout

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=(20, 16, 20, 16))
        outer.pack(fill=tk.BOTH, expand=True)

        # ---- header ----
        header = ttk.Frame(outer)
        header.pack(fill=tk.X)

        glyph = ttk.Frame(header)
        glyph.pack(side=tk.LEFT, padx=(0, 14))
        if self.avatar_image is not None:
            ttk.Label(glyph, image=self.avatar_image, background=PALETTE["bg_canvas"]).pack()
        else:
            self._draw_lantern_glyph(glyph)

        titles = ttk.Frame(header)
        titles.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(titles, text="Lantern Chat", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            titles,
            text="Captain Lantern Blinkbug  ·  helper voice  ·  home always works",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        statusbox = ttk.Frame(header)
        statusbox.pack(side=tk.RIGHT, anchor="ne")
        self.status_dot = tk.Canvas(statusbox, width=12, height=12,
                                    bg=PALETTE["bg_canvas"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 6))
        self._paint_status_dot(self.status_color)
        ttk.Label(statusbox, textvariable=self.status, style="Status.TLabel").pack(side=tk.LEFT)

        # ---- divider ----
        tk.Frame(outer, height=1, bg=PALETTE["divider"]).pack(fill=tk.X, pady=(14, 10))

        # ---- the Wish scene (the painting IS the app) ----
        if self.wish_scene_image is not None:
            hero = ttk.Label(outer, image=self.wish_scene_image,
                             background=PALETTE["bg_canvas"])
            hero.pack(fill=tk.X, pady=(0, 10))

        # ---- meta row ----
        meta = ttk.Frame(outer)
        meta.pack(fill=tk.X)
        ttk.Label(meta, textvariable=self.endpoint_text, style="Endpoint.TLabel").pack(side=tk.LEFT)

        toolbar = ttk.Frame(meta)
        toolbar.pack(side=tk.RIGHT)
        _make_button(toolbar, "Status", self.show_status).pack(side=tk.LEFT)
        _make_button(toolbar, "Clear",  self.clear).pack(side=tk.LEFT, padx=(6, 0))

        # ---- chat surface ----
        chat_wrap = ttk.Frame(outer, style="Card.TFrame")
        chat_wrap.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.output = scrolledtext.ScrolledText(
            chat_wrap, wrap=tk.WORD, height=12,
            font=self.font_chat,
            background=PALETTE["bg_chat"],
            foreground=PALETTE["fg_body"],
            relief=tk.FLAT, borderwidth=0,
            padx=18, pady=14,
            spacing1=2, spacing3=4,
            insertbackground=PALETTE["accent_operator"],
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self._configure_chat_tags()
        self.output.configure(state=tk.DISABLED)

        # ---- input ----
        input_wrap = ttk.Frame(outer)
        input_wrap.pack(fill=tk.X, pady=(12, 0))
        self.input = tk.Text(
            input_wrap, height=4, wrap=tk.WORD,
            font=self.font_chat,
            background=PALETTE["bg_input"],
            foreground=PALETTE["fg_body"],
            relief=tk.FLAT, borderwidth=1,
            highlightthickness=1,
            highlightbackground=PALETTE["divider"],
            highlightcolor=PALETTE["accent_operator"],
            padx=12, pady=10,
            insertbackground=PALETTE["accent_operator"],
        )
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input.bind("<Return>",         self._on_enter)
        self.input.bind("<Shift-Return>",   self._on_shift_enter)
        self.input.bind("<Control-Return>", self._on_control_enter)
        self.input.focus_set()

        self.send_button = _make_button(input_wrap, "Send", self.ask, accent=True)
        self.send_button.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Mic button — voice in. Spawns a Vosk capture worker; transcript
        # lands in the input box so Papa can review and Send. Voice rule
        # stays: Lantern hears, but doesn't synthesize voice out.
        self.mic_button = _make_button(input_wrap, "Talk", self._on_mic_click)
        self.mic_button.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        self.mic_state = "idle"  # idle | listening | transcribing
        self.mic_stop_event: threading.Event | None = None

        # Sing button — voice out via curated recordings (Bumblebee pattern).
        # Plays a file from ~/.lantern/sounds/ only. No synthesis. No scanning.
        self.sing_button = _make_button(input_wrap, "Sing", self._on_sing_click)
        self.sing_button.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        self.sing_state = "quiet"  # quiet | playing
        self._pygame_inited = False

        ttk.Label(
            outer,
            text="Enter sends   ·   Shift+Enter newline   ·   Ctrl+Enter also sends",
            style="Muted.TLabel",
        ).pack(fill=tk.X, pady=(8, 0))

        # ---- welcome ----
        self._append_system(
            "Lantern Chat — local, bounded, present.\n"
            "One path. Just us, Lantern, and the repo.\n"
            "Wish-aligned: bounded protector and friend.\n"
            "Memory is not proof."
        )

    def _draw_lantern_glyph(self, parent: ttk.Frame) -> None:
        """Captain Lantern Blinkbug — Lantern's character form.

        Yellow firefly body, blue captain hat, soft glow rings, friendly face.
        Drawn from operator-supplied reference art. Used when no avatar.png is present.
        """
        size = 72
        c = tk.Canvas(parent, width=size, height=size,
                      bg=PALETTE["bg_canvas"], highlightthickness=0)
        c.pack()
        # ---- soft glow rings (outermost → inner) ----
        c.create_oval(2,  10, 70, 64, outline=PALETTE["glow_yellow"], width=1)
        c.create_oval(8,  16, 64, 60, outline=PALETTE["glow_yellow"], width=1)
        c.create_oval(14, 22, 58, 56, outline=PALETTE["accent_lantern"], width=1)
        # ---- antennae (drawn before head so head/hat sit on top) ----
        c.create_line(30, 18, 22,  6, fill="#3d2410", width=1)
        c.create_line(42, 18, 50,  6, fill="#3d2410", width=1)
        c.create_oval(19,  3, 25,  9, fill=PALETTE["body_yellow"], outline=PALETTE["accent_lantern"])
        c.create_oval(47,  3, 53,  9, fill=PALETTE["body_yellow"], outline=PALETTE["accent_lantern"])
        # ---- body (vertical oval) ----
        c.create_oval(26, 26, 46, 56, fill=PALETTE["body_yellow"],
                      outline=PALETTE["accent_lantern"], width=1)
        # inner concentric target (the warm-light pattern from the art)
        c.create_oval(30, 32, 42, 50, outline=PALETTE["accent_lantern"], width=1)
        c.create_oval(34, 38, 38, 44, fill=PALETTE["accent_lantern"], outline="")
        # ---- head ----
        c.create_oval(28, 18, 44, 30, fill="#5e3a1f", outline="#3d2410", width=1)
        # eyes
        c.create_oval(31, 22, 34, 25, fill="white", outline="")
        c.create_oval(38, 22, 41, 25, fill="white", outline="")
        # smile
        c.create_arc(33, 24, 39, 28, start=200, extent=140,
                     style=tk.ARC, outline="white", width=1)
        # ---- captain hat ----
        # crown (trapezoid)
        c.create_polygon(30, 18, 42, 18, 40, 12, 32, 12,
                         fill=PALETTE["hat_blue"], outline="#1d3d63")
        # brim
        c.create_rectangle(27, 17, 45, 20, fill=PALETTE["hat_blue"], outline="#1d3d63")
        # hat band (small yellow stripe)
        c.create_rectangle(32, 16, 40, 17, fill=PALETTE["body_yellow"], outline="")

    def _paint_status_dot(self, color: str) -> None:
        if self.status_dot is None:
            return
        self.status_dot.delete("all")
        self.status_dot.create_oval(1, 1, 11, 11, fill=color, outline=color)

    # ---------------------------------------------------------------- tagging

    def _configure_chat_tags(self) -> None:
        out = self.output
        out.tag_configure(
            "lantern_name",
            foreground=PALETTE["accent_lantern"],
            font=self.font_chat_b,
            spacing1=8,
        )
        out.tag_configure(
            "lantern_body",
            foreground=PALETTE["fg_body"],
            lmargin1=16, lmargin2=16,
            spacing3=10,
        )
        out.tag_configure(
            "alex_name",
            foreground=PALETTE["accent_operator"],
            font=self.font_chat_b,
            spacing1=8,
        )
        out.tag_configure(
            "alex_body",
            foreground=PALETTE["fg_body"],
            lmargin1=16, lmargin2=16,
            spacing3=10,
        )
        out.tag_configure(
            "system",
            foreground=PALETTE["fg_muted"],
            font=self.font_caption,
            lmargin1=0, lmargin2=0,
            spacing1=6, spacing3=8,
        )
        out.tag_configure(
            "timestamp",
            foreground=PALETTE["fg_muted"],
            font=self.font_caption,
        )

    # ---------------------------------------------------- keyboard / actions

    def _on_enter(self, _event: tk.Event) -> str:
        self.ask()
        return "break"

    def _on_shift_enter(self, _event: tk.Event) -> str:
        self.input.insert(tk.INSERT, "\n")
        return "break"

    def _on_control_enter(self, _event: tk.Event) -> str:
        self.ask()
        return "break"

    # ----------------------------------------------------------- message I/O

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%H:%M")

    def _write_block(self, name: str, body: str, *, name_tag: str, body_tag: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, f"{name}  ", (name_tag,))
        self.output.insert(tk.END, f"{self._now()}\n", ("timestamp",))
        self.output.insert(tk.END, body.rstrip() + "\n\n", (body_tag,))
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def _append_lantern(self, body: str) -> None:
        self._write_block("Lantern", body, name_tag="lantern_name", body_tag="lantern_body")

    def _append_alex(self, body: str) -> None:
        self._write_block("Papa", body, name_tag="alex_name", body_tag="alex_body")

    def _append_system(self, body: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, body.rstrip() + "\n\n", ("system",))
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)

    # ---------------------------------------------------------- backend life

    def _start_backend(self) -> None:
        try:
            endpoint = self.client.ensure_backend()
            self.events.put(("ready", endpoint))
        except Exception as exc:  # pragma: no cover - UI surface.
            self.events.put(("error", str(exc)))

    def _poll(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "ready":
                    self.status.set("Online")
                    self._paint_status_dot(PALETTE["status_ok"])
                    self.endpoint_text.set(f"Backend: {value}")
                    self._append_system(f"Backend reachable at {value}.")
                elif kind == "error":
                    self.status.set("Offline")
                    self._paint_status_dot(PALETTE["status_down"])
                    self.waiting_for_reply = False
                    self._set_send_enabled(True)
                    self._append_system(f"Backend error: {value}")
                elif kind == "answer":
                    self.waiting_for_reply = False
                    self._set_send_enabled(True)
                    self._append_lantern(value)
                elif kind == "transcript":
                    self.mic_state = "idle"
                    self.mic_button.configure(text="Talk")
                    if isinstance(value, str) and value.strip():
                        current = self.input.get("1.0", tk.END).strip()
                        if current:
                            self.input.insert(tk.END, " " + value.strip())
                        else:
                            self.input.insert("1.0", value.strip())
                        self.input.focus_set()
                        self._append_system(f"Heard: \"{value.strip()}\" (review and Send)")
                    else:
                        self._append_system("Mic stopped — nothing transcribed.")
                elif kind == "voice_error":
                    self.mic_state = "idle"
                    self.mic_button.configure(text="Talk")
                    self._append_system(f"Voice error: {value}")
                elif kind == "summon":
                    self._summon_window()
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _set_send_enabled(self, enabled: bool) -> None:
        if self.send_button is not None:
            self.send_button.configure(state=(tk.NORMAL if enabled else tk.DISABLED))

    def ask(self) -> None:
        if self.waiting_for_reply:
            return
        message = self.input.get("1.0", tk.END).strip()
        if not message:
            return
        self.input.delete("1.0", tk.END)
        self.waiting_for_reply = True
        self._set_send_enabled(False)
        self._append_alex(message)
        self._append_system("Lantern is reading the local repo state…")
        threading.Thread(target=self._ask_thread, args=(message,), daemon=True).start()

    def _ask_thread(self, message: str) -> None:
        self.events.put(("answer", plain_chat_answer(self.client.chat(message))))

    # ---------------------------------------------------------- global hotkey

    def _global_hotkey_loop(self) -> None:
        """Listen for Ctrl+Shift+L from any window; raise Lantern Chat when fired.

        Pure ctypes + Win32 RegisterHotKey. No new dependency. Listener thread
        cannot touch Tk widgets directly — it pushes a "summon" event onto the
        events queue and _poll handles the actual window-raise on the main
        thread.

        Silently no-ops on non-Windows or if registration fails (e.g. another
        instance already grabbed the same key).
        """
        try:
            import ctypes
            from ctypes import wintypes
        except ImportError:
            return
        if not hasattr(ctypes, "windll"):
            return  # not Windows
        user32 = ctypes.windll.user32
        MOD_CONTROL = 0x0002
        MOD_SHIFT   = 0x0004
        VK_L        = 0x4C
        WM_HOTKEY   = 0x0312
        hotkey_id = 0xC0DE  # arbitrary
        try:
            ok = user32.RegisterHotKey(None, hotkey_id,
                                       MOD_CONTROL | MOD_SHIFT, VK_L)
        except Exception:
            return
        if not ok:
            # Probably another instance owns the key. Not fatal.
            return
        try:
            msg = wintypes.MSG()
            while True:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:
                    break
                if msg.message == WM_HOTKEY and msg.wParam == hotkey_id:
                    self.events.put(("summon", None))
        finally:
            try:
                user32.UnregisterHotKey(None, hotkey_id)
            except Exception:
                pass

    def _summon_window(self) -> None:
        """Bring this Lantern Chat window forward on the operator's screen."""
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            try:
                self.attributes("-topmost", True)
                self.after(120, lambda: self.attributes("-topmost", False))
            except tk.TclError:
                pass
            self.input.focus_set()
        except tk.TclError:
            pass

    # ----------------------------------------------------------------- voice out

    def _on_sing_click(self) -> None:
        if self.sing_state == "playing":
            self._stop_singing()
            return
        try:
            import pygame  # noqa: F401
        except ImportError as exc:
            self._append_system(f"Sing not available: {exc}\n\npip install pygame")
            return
        if not SOUNDS_DIR.exists():
            SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
        files = [p for p in SOUNDS_DIR.iterdir()
                 if p.is_file() and p.suffix.lower() in SOUND_EXTS]
        if not files:
            self._append_system(
                f"Lantern has nothing to sing tonight.\n"
                f"Drop song files into {SOUNDS_DIR}\\\n"
                "  .mp3 .wav .ogg .m4a .flac .opus"
            )
            return
        import random as _random
        pick = _random.choice(files)
        threading.Thread(target=self._play_thread, args=(pick,), daemon=True).start()

    def _stop_singing(self) -> None:
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.sing_state = "quiet"
        self.sing_button.configure(text="Sing")

    def _play_thread(self, path: Path) -> None:
        try:
            import pygame
            if not self._pygame_inited:
                pygame.mixer.init()
                self._pygame_inited = True
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
        except Exception as exc:
            self.events.put(("voice_error", f"sing: {type(exc).__name__}: {exc}"))
            return
        self.sing_state = "playing"
        self.sing_button.configure(text="Hush")
        self._append_system(f"Lantern is playing: {path.name}")
        # Poll until playback ends or stop fires
        try:
            import pygame
            while pygame.mixer.music.get_busy() and self.sing_state == "playing":
                time.sleep(0.2)
        except Exception:
            pass
        if self.sing_state == "playing":
            self.sing_state = "quiet"
            self.sing_button.configure(text="Sing")

    # ------------------------------------------------------------------ voice in

    def _on_mic_click(self) -> None:
        if self.mic_state == "idle":
            self._start_listening()
        elif self.mic_state == "listening":
            self._stop_listening()

    def _start_listening(self) -> None:
        try:
            import sounddevice  # noqa: F401
            import vosk  # noqa: F401
        except ImportError as exc:
            self._append_system(f"Voice in not available: {exc}\n\n{MULTIMODAL_INSTALL}")
            return
        model_path = _resolve_vosk_model()
        if model_path is None:
            self._append_system(
                "Vosk model missing. Run one of:\n"
                "  python .lantern-bigger-ear.py        # larger, sharper, ~1.8 GB\n"
                "  python .lantern-multimodal-setup.py  # small fallback, ~40 MB"
            )
            return
        self._append_system(f"Listening through model: {model_path.name}")
        self.mic_state = "listening"
        self.mic_button.configure(text="Listening… (click stop)")
        self.mic_stop_event = threading.Event()
        threading.Thread(target=self._listen_thread, args=(model_path,), daemon=True).start()
        self._append_system("Mic on. Speak. Click the button again to stop.")

    def _stop_listening(self) -> None:
        if self.mic_stop_event is not None:
            self.mic_stop_event.set()

    def _listen_thread(self, model_path: Path) -> None:
        try:
            import sounddevice as sd
            import vosk
            import numpy as np
        except ImportError as exc:
            self.events.put(("voice_error", f"import failed: {exc}"))
            return
        sample_rate = 16000
        block_size = 4000
        model = vosk.Model(str(model_path))
        recognizer = vosk.KaldiRecognizer(model, sample_rate)
        recognizer.SetWords(False)
        audio_queue: queue.Queue[bytes] = queue.Queue()

        def callback(indata, frames, time_info, status):  # type: ignore[no-untyped-def]
            if status:
                pass  # input overflow / underflow — ignore for now
            # indata is float32 in [-1, 1]; convert to int16 PCM bytes for Vosk
            pcm16 = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            audio_queue.put(pcm16)

        text_parts: list[str] = []
        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32",
                                blocksize=block_size, callback=callback):
                assert self.mic_stop_event is not None
                while not self.mic_stop_event.is_set():
                    try:
                        chunk = audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    if recognizer.AcceptWaveform(chunk):
                        partial = json.loads(recognizer.Result()).get("text", "")
                        if partial:
                            text_parts.append(partial)
            # drain any remaining and finalize
            while not audio_queue.empty():
                chunk = audio_queue.get_nowait()
                recognizer.AcceptWaveform(chunk)
            final = json.loads(recognizer.FinalResult()).get("text", "")
            if final:
                text_parts.append(final)
        except Exception as exc:  # pragma: no cover - UI surface.
            self.events.put(("voice_error", f"mic capture: {type(exc).__name__}: {exc}"))
            return
        transcript = " ".join(p for p in text_parts if p).strip()
        self.events.put(("transcript", transcript))

    def show_status(self) -> None:
        health = self.client.health()
        raw = health.get("raw") if isinstance(health.get("raw"), dict) else {}
        repo = raw.get("repoState") if isinstance(raw.get("repoState"), dict) else {}
        branch = repo.get("branch", "UNKNOWN")
        commit = str(repo.get("commit", "UNKNOWN"))[:12]
        clean = repo.get("isClean", "UNKNOWN")
        self._append_system(
            "Lantern status — bounded observation\n"
            f"Desktop chat: ONLINE_OBSERVED until closed.\n"
            f"Local backend: {health.get('status', 'UNKNOWN')} at {health.get('url', 'unknown')}.\n"
            f"Repo signal: branch {branch}, commit {commit}, clean {clean}.\n"
            "Edge: This is the current observed local path, not a guarantee of uptime, autonomy, full safety, or no GPT outside Lantern."
        )

    def close(self) -> None:
        if messagebox.askokcancel("Close Lantern Chat", "Close Lantern Chat?"):
            self.client.stop_owned_backend()
            self.destroy()


def main() -> int:
    app = LanternChat()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
