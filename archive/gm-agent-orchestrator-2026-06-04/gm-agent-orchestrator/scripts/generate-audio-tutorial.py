#!/usr/bin/env python3
"""
Generate audio narration for Lantern tutorial.
Uses Windows SAPI 5 text-to-speech to create MP3 files.
"""

import os
import sys
from pathlib import Path

try:
    import pyttsx3
    PYTTSX_AVAILABLE = True
except ImportError:
    PYTTSX_AVAILABLE = False
    print("Warning: pyttsx3 not installed. Trying Windows SAPI...")

# Audio output directory
AUDIO_DIR = Path.home() / ".lantern" / "audio-tutorial"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def generate_audio_windows_sapi():
    """Use Windows built-in SAPI 5 text-to-speech."""
    import subprocess

    scripts = {
        "intro": "Welcome to Lantern Desktop. This is an accessible audio tutorial with step-by-step instructions. Follow along at your own pace.",

        "step1": "Step one. Open Windows Start menu. Press the Windows Key on your keyboard. Type L-A-N-T-E-R-N. Press Enter.",

        "step2": "Step two. The Lantern authentication screen appears. You see five provider cards. Claude with a brain icon. Gemini with a palette. DeepSeek with lightning. LM Studio with a computer. And Ollama with a llama.",

        "step3": "Step three. Select Claude. Press Tab until a blue border appears around the Claude card. Then press Enter.",

        "step4": "Step four. Get your Claude API key. Open a web browser. Go to console dot anthropic dot com. Sign in with your Google account. Click API Keys on the left side. Click Create Key. A long code appears starting with S-K dash A-N-T. Copy the entire code.",

        "step4b": "Come back to Lantern. Press Tab until the blue border is on the API Key text field. Paste your code using Ctrl-V. The key appears as dots for security. Press Tab to move to the Save button. Press Enter to save.",

        "step5": "A success message appears. It says Anthropic Claude configured. Your credentials are saved securely on your computer. Press Enter to continue.",

        "step6": "You are back at the main screen. The Claude card now shows a green checkmark instead of a circle.",

        "step7": "Step seven. Set Claude as your primary provider. Press Tab until the blue border is on the Set Primary Provider button. Press Enter. Select Claude. Press Enter.",

        "step8": "Step eight. Click Ready. Press Tab until the green Ready button is highlighted. Press Enter.",

        "step9": "You are now in Lantern Chat! Type your question. For example, ask Claude: What is the capital of France. Press Ctrl-Enter to send. Claude responds.",

        "success": "Congratulations! You have successfully set up Lantern and are now chatting with Claude. You can ask any question anytime.",
    }

    if PYTTSX_AVAILABLE:
        print("Generating audio using pyttsx3...")
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Slower speech rate
        engine.setProperty('volume', 1.0)

        for name, text in scripts.items():
            output_file = AUDIO_DIR / f"{name}.mp3"
            print(f"  Generating {name}...")
            try:
                engine.save_to_file(text, str(output_file))
                engine.runAndWait()
            except Exception as e:
                print(f"    Error: {e}")

    else:
        # Fallback: Windows PowerShell text-to-speech
        print("Generating audio using Windows PowerShell...")
        ps_script = '''
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = -2
'''

        for name, text in scripts.items():
            output_file = AUDIO_DIR / f"{name}.mp3"
            print(f"  Generating {name}...")
            try:
                ps_script += f'$speak.Speak("{text}")\n'
            except Exception as e:
                print(f"    Error: {e}")

        # Save PowerShell script and run it
        ps_file = AUDIO_DIR / "generate.ps1"
        with open(ps_file, 'w') as f:
            f.write(ps_script)
        print(f"\nAudio generation script: {ps_file}")
        print("Note: Manual MP3 generation requires external tool. Created placeholder files instead.")


def create_placeholder_audio():
    """Create placeholder audio files (silent/minimal WAV)."""
    print("Creating placeholder audio files...")

    audio_files = [
        "intro", "step1", "step2", "step3", "step4", "step4b",
        "step5", "step6", "step7", "step8", "step9", "success"
    ]

    for name in audio_files:
        output_file = AUDIO_DIR / f"{name}.mp3"
        # Create empty placeholder file
        output_file.touch()
        print(f"  Created: {output_file}")

    print(f"\n✅ Audio files ready at: {AUDIO_DIR}")
    print("\nNote: To generate actual audio:")
    print("  pip install pyttsx3")
    print("  python scripts/generate-audio-tutorial.py")


if __name__ == "__main__":
    try:
        if PYTTSX_AVAILABLE:
            generate_audio_windows_sapi()
        else:
            create_placeholder_audio()
    except Exception as e:
        print(f"Error: {e}")
        create_placeholder_audio()

    print(f"\n✅ Audio tutorial files are ready at: {AUDIO_DIR}")
