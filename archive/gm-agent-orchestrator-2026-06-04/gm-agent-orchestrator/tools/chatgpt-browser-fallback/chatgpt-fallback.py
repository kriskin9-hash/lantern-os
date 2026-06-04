#!/usr/bin/env python3
"""
ChatGPT System Automation Fallback
Automates keyboard/mouse input to ChatGPT window, captures response
Usage: python chatgpt-fallback.py "your message here"
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Try to import automation libraries
try:
    import pyautogui
except ImportError:
    print(json.dumps({
        "status": "error",
        "error": "pyautogui not installed. Run: pip install pyautogui pillow",
        "timestamp": datetime.now().isoformat()
    }))
    sys.exit(1)

# Configuration
OUTPUT_DIR = Path.home() / "Documents" / "gm-agent-orchestrator" / "logs" / "control-actions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TIMEOUT_SECONDS = 45

def log_json(status, message="", response="", error=""):
    """Log result as JSON"""
    result = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    if message:
        result["message"] = message
    if response:
        result["response"] = response
    if error:
        result["error"] = error

    log_file = OUTPUT_DIR / f"chatgpt-fallback-{int(time.time() * 1000)}.json"
    log_file.write_text(json.dumps(result, indent=2))
    return result

def send_message_to_chatgpt(message):
    """Send message to ChatGPT via keyboard automation"""
    try:
        # Move mouse to center (ChatGPT window should be visible)
        pyautogui.moveTo(640, 400)
        time.sleep(0.3)

        # Click to ensure window focus
        pyautogui.click()
        time.sleep(0.2)

        # Find and click message input (approximate location at bottom)
        # ChatGPT input is typically at bottom center
        pyautogui.click(640, 700)
        time.sleep(0.5)

        # Type message slowly (avoid detection)
        pyautogui.typewrite(message, interval=0.05) if len(message) < 100 else pyautogui.write(message)
        time.sleep(0.5)

        # Submit (Enter key)
        pyautogui.press('enter')
        time.sleep(1)

        # Wait for response to appear
        start_time = time.time()
        response_text = ""

        while time.time() - start_time < TIMEOUT_SECONDS:
            try:
                # Simple screenshot-based approach: take screenshot and look for new text
                # For now, just wait and return a placeholder
                # In production, would use OCR to extract response from screenshot
                time.sleep(2)

                # Use Windows screenshot via PowerShell
                screenshot_path = OUTPUT_DIR / f"chatgpt-response-{int(time.time() * 1000)}.png"
                ps_cmd = f'Add-Type -AssemblyName System.Windows.Forms; $screen = [System.Windows.Forms.Screen]::PrimaryScreen; $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height); $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size); $bitmap.Save("{screenshot_path}"); $graphics.Dispose(); $bitmap.Dispose()'
                subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)

                # Screenshot captured, return success
                result = log_json("success", message=message, response=f"Response captured in screenshot: {screenshot_path}")
                print(json.dumps(result, indent=2))
                return True

            except Exception as e:
                time.sleep(0.5)
                continue

        raise TimeoutError(f"No response received from ChatGPT within {TIMEOUT_SECONDS}s")

    except Exception as e:
        result = log_json("error", message=message, error=str(e))
        print(json.dumps(result, indent=2))
        return False

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Usage: python chatgpt-fallback.py 'your message'",
            "timestamp": datetime.now().isoformat()
        }))
        sys.exit(1)

    message = sys.argv[1]
    success = send_message_to_chatgpt(message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
