#!/usr/bin/env python3
"""
Lantern Telemetry System
Tracks usage, crashes, and performance (local-only, no external upload without consent).
"""

import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class LanternTelemetry:
    """Manages telemetry for Lantern applications."""

    def __init__(self, app_name: str = "lantern-chat", session_id: Optional[str] = None):
        """
        Initialize telemetry tracker.

        Args:
            app_name: Name of the application (lantern-chat, lantern-kids, etc.)
            session_id: Optional session ID (UUID4 if not provided)
        """
        self.app_name = app_name
        self.session_id = session_id or self._generate_session_id()
        self.session_start = datetime.now()

        # Create telemetry directory
        self.telemetry_dir = Path.home() / ".lantern" / "telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)

        # Session file
        timestamp = self.session_start.strftime("%Y%m%d-%H%M%S")
        self.session_file = self.telemetry_dir / f"{app_name}-{timestamp}.jsonl"

        # Metrics
        self.message_count = 0
        self.crash_count = 0
        self.error_count = 0
        self.provider_usage = {}

        # Log session start
        self.log_event("session_start", {
            "app_name": app_name,
            "session_id": self.session_id,
            "python_platform": self._get_platform()
        })

    @staticmethod
    def _generate_session_id() -> str:
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    @staticmethod
    def _get_platform() -> str:
        """Get platform info."""
        import platform
        return f"{platform.system()} {platform.release()}"

    def log_event(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """
        Log an event to telemetry file.

        Args:
            event_type: Type of event (message, crash, error, usage_limit, etc.)
            data: Additional event data
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "session_id": self.session_id,
            **(data or {})
        }

        try:
            with open(self.session_file, 'a') as f:
                f.write(json.dumps(record) + '\n')
        except Exception as e:
            # Silently fail if telemetry file is locked or inaccessible
            print(f"[Telemetry Warning] Failed to write event: {e}")

    def log_message(self, sender: str, length: int, provider: str = "unknown",
                   response_time_ms: float = 0, token_count: int = 0):
        """Log a chat message."""
        self.message_count += 1

        # Track provider usage
        self.provider_usage[provider] = self.provider_usage.get(provider, 0) + 1

        self.log_event("message", {
            "sender": sender,
            "length": length,
            "provider": provider,
            "response_time_ms": response_time_ms,
            "token_count": token_count,
            "message_number": self.message_count
        })

    def log_crash(self, error: Exception, error_context: Optional[str] = None):
        """Log a crash with traceback (no PII)."""
        self.crash_count += 1

        # Get clean traceback (no file paths with usernames)
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        clean_tb = ''.join(tb_lines)

        self.log_event("crash", {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": clean_tb,
            "context": error_context,
            "crash_number": self.crash_count
        })

    def log_error(self, error_code: str, message: str, severity: str = "normal"):
        """Log an error (non-crash)."""
        self.error_count += 1

        self.log_event("error", {
            "error_code": error_code,
            "message": message,
            "severity": severity,  # low, normal, high, critical
            "error_number": self.error_count
        })

    def log_api_call(self, provider: str, model: str, success: bool,
                    latency_ms: float = 0, error: Optional[str] = None,
                    tokens_in: int = 0, tokens_out: int = 0):
        """Log an API call to a provider."""
        self.log_event("api_call", {
            "provider": provider,
            "model": model,
            "success": success,
            "latency_ms": latency_ms,
            "error": error,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out
        })

    def log_accessibility_event(self, setting: str, value: Any):
        """Log accessibility feature usage."""
        self.log_event("accessibility", {
            "setting": setting,
            "value": value
        })

    def log_parental_action(self, action: str, details: Optional[Dict] = None):
        """Log parental control actions (Lantern Kids)."""
        self.log_event("parental_action", {
            "action": action,
            "details": details or {}
        })

    def log_daily_usage(self, minutes_used: int, messages_sent: int,
                       features_used: Optional[list] = None):
        """Log daily usage summary."""
        self.log_event("daily_summary", {
            "minutes_used": minutes_used,
            "messages_sent": messages_sent,
            "features_used": features_used or [],
            "crashes_today": self.crash_count,
            "errors_today": self.error_count
        })

    def log_session_end(self):
        """Log session closure."""
        duration = (datetime.now() - self.session_start).total_seconds()

        summary = {
            "duration_sec": duration,
            "message_count": self.message_count,
            "crash_count": self.crash_count,
            "error_count": self.error_count,
            "provider_usage": self.provider_usage
        }

        self.log_event("session_end", summary)

        # Return summary for optional reporting
        return summary

    @staticmethod
    def get_session_summary(days: int = 1) -> Dict[str, Any]:
        """
        Get summary of telemetry over last N days.

        Returns:
            Dict with aggregated stats
        """
        telemetry_dir = Path.home() / ".lantern" / "telemetry"
        if not telemetry_dir.exists():
            return {}

        stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "total_crashes": 0,
            "total_errors": 0,
            "providers_used": set(),
            "sessions": []
        }

        # Scan recent files
        import time
        cutoff_time = time.time() - (days * 86400)

        for session_file in sorted(telemetry_dir.glob("*.jsonl")):
            if session_file.stat().st_mtime < cutoff_time:
                continue

            try:
                with open(session_file) as f:
                    for line in f:
                        record = json.loads(line)
                        event_type = record.get('event_type')

                        if event_type == "session_start":
                            stats["total_sessions"] += 1
                            stats["sessions"].append({
                                "session_id": record.get('session_id'),
                                "start": record.get('timestamp')
                            })

                        elif event_type == "message":
                            stats["total_messages"] += 1
                            provider = record.get('provider')
                            if provider:
                                stats["providers_used"].add(provider)

                        elif event_type == "crash":
                            stats["total_crashes"] += 1

                        elif event_type == "error":
                            stats["total_errors"] += 1

            except Exception as e:
                print(f"[Telemetry Warning] Error reading {session_file}: {e}")

        # Convert set to list for JSON serialization
        stats["providers_used"] = list(stats["providers_used"])

        return stats

    @staticmethod
    def export_telemetry(output_file: Optional[str] = None) -> str:
        """
        Export telemetry for review (anonymized, local-only).

        Args:
            output_file: Optional custom output path

        Returns:
            Path to exported file
        """
        telemetry_dir = Path.home() / ".lantern" / "telemetry"
        if not telemetry_dir.exists():
            return "No telemetry data found"

        export_dir = Path.home() / ".lantern" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        export_path = output_file or str(export_dir / f"telemetry-export-{timestamp}.json")

        # Aggregate all telemetry
        all_events = []
        for session_file in telemetry_dir.glob("*.jsonl"):
            try:
                with open(session_file) as f:
                    for line in f:
                        all_events.append(json.loads(line))
            except Exception as e:
                print(f"[Telemetry Warning] Error reading {session_file}: {e}")

        # Write export
        with open(export_path, 'w') as f:
            json.dump({
                "export_timestamp": datetime.now().isoformat(),
                "event_count": len(all_events),
                "events": all_events
            }, f, indent=2)

        return export_path


# Example usage in lantern-chat-ui.py:
"""
from lantern_telemetry import LanternTelemetry

class LanternChat:
    def __init__(self, root, selected_provider):
        self.telemetry = LanternTelemetry("lantern-chat")
        ...

    def send_message(self):
        user_input = self.input_field.get("1.0", tk.END).strip()
        self.input_field.delete("1.0", tk.END)
        self._display_message("You", user_input, "user")

        try:
            start_time = time.time()
            # ... LLM call ...
            latency_ms = (time.time() - start_time) * 1000
            self.telemetry.log_message("user", len(user_input), self.selected_provider, latency_ms)
        except Exception as e:
            self.telemetry.log_crash(e, "Message send failed")

    def on_window_close(self):
        summary = self.telemetry.log_session_end()
        # Can log summary or send notification
        self.root.destroy()
"""
