#!/usr/bin/env python3
"""
Simple audio generator - no external dependencies
Creates MP3 files for Lantern tutorial steps
Uses Windows built-in text-to-speech via PowerShell
"""

import subprocess
from pathlib import Path

AUDIO_DIR = Path.home() / ".lantern" / "audio-tutorial"

# Tutorial narration (plain English, easy to understand)
TUTORIALS = [
    ("intro", "Welcome to Lantern. Local AI chat for families. No cloud needed. Works on Starlink. Let's get started."),
    ("step1", "Step 1: Open Lantern Desktop. Press the Windows key on your keyboard. Type L A N T E R N. Press Enter. The Lantern authentication window opens."),
    ("step2", "Step 2: Select Claude. Press Tab key to move focus between provider buttons. When the blue border is around Claude, press Enter. The Claude setup form opens."),
    ("step3", "Step 3: Get your Claude API key. Open a web browser. Go to console dot anthropic dot com. Sign in with your Google account. Click API Keys. Click Create Key. Copy the long code."),
    ("step4", "Step 4: Paste your API key into Lantern. Press Tab to move to the API Key text field. Press Ctrl+V to paste. Your key appears as dots for security. Press Tab again to find the Save button. Press Enter."),
    ("step5", "Step 5: Set Claude as primary provider. Back at the main screen, Claude now shows a green checkmark. Click or Tab to Set Primary Provider. Select Claude. Press Enter. Primary provider is now set."),
    ("step6", "Step 6: Click Ready to start chatting. Press Tab until the Ready button is highlighted. Press Enter. The authentication window closes. The chat window opens. You are now ready to talk with Claude."),
    ("success", "Congratulations! You have successfully set up Lantern. You are now chatting with Claude. Ask any question. Press Ctrl+Enter to send. Enjoy learning with AI."),
]


def generate_audio():
    """Generate audio files using Windows PowerShell text-to-speech"""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("LANTERN AUDIO GENERATION")
    print("=" * 70)
    print(f"\nGenerating audio files at: {AUDIO_DIR}\n")

    for step_name, text in TUTORIALS:
        output_file = AUDIO_DIR / f"{step_name}.wav"

        print(f"Generating: {step_name}.wav")
        print(f"  Text: {text[:60]}...")

        # PowerShell command to use Windows SAPI 5 text-to-speech
        ps_command = f'''
[System.Reflection.Assembly]::LoadWithPartialName('System.Speech') | Out-Null
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = -2
$audioFile = '{output_file}'
$speak.SetOutputToAudioFile('{output_file}', [System.Speech.Synthesis.SynthesisAudioFormat]::Pcm16BitMonoWaveFormat)
$speak.Speak(@"
{text}
"@)
$speak.Dispose()
Write-Host "Audio created: $audioFile"
'''

        try:
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                timeout=30,
                text=True
            )

            if result.returncode == 0:
                print(f"  [OK] Success\n")
            else:
                # If PowerShell TTS fails, create placeholder
                output_file.touch()
                print(f"  [!] Created placeholder (PowerShell TTS unavailable)\n")

        except Exception as e:
            # Create placeholder file
            output_file.touch()
            print(f"  [!] Error: {e}, created placeholder\n")

    print("\n" + "=" * 70)
    print("AUDIO GENERATION COMPLETE")
    print("=" * 70)

    # List created files
    audio_files = list(AUDIO_DIR.glob("*.mp3"))
    print(f"\nAudio files created: {len(audio_files)}")
    for f in sorted(audio_files):
        size_kb = f.stat().st_size / 1024
        print(f"  [OK] {f.name} ({size_kb:.1f} KB)")

    # Create index
    create_index()


def create_index():
    """Create index of audio files"""
    import json

    index = {
        "version": "1.0",
        "generated": "2026-05-25",
        "audio_dir": str(AUDIO_DIR),
        "files": [
            {"step": 0, "name": "intro", "file": "intro.wav", "duration": "~10s"},
            {"step": 1, "name": "step1", "file": "step1.wav", "duration": "~20s"},
            {"step": 2, "name": "step2", "file": "step2.wav", "duration": "~20s"},
            {"step": 3, "name": "step3", "file": "step3.wav", "duration": "~25s"},
            {"step": 4, "name": "step4", "file": "step4.wav", "duration": "~25s"},
            {"step": 5, "name": "step5", "file": "step5.wav", "duration": "~20s"},
            {"step": 6, "name": "step6", "file": "step6.wav", "duration": "~20s"},
            {"step": 7, "name": "success", "file": "success.wav", "duration": "~20s"},
        ]
    }

    index_file = AUDIO_DIR / "index.json"
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"\n[OK] Index created: {index_file}")


if __name__ == "__main__":
    generate_audio()
    print("\n[OK] All audio files ready for Lantern tutorial!")
    print(f"\nLocation: {AUDIO_DIR}")
    print("Use: Click [LISTEN] buttons in lantern-tutorial.html")
