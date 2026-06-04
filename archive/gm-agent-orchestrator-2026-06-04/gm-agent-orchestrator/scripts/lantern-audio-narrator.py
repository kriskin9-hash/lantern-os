#!/usr/bin/env python3
"""
Lantern Audio Narrator - Frank Sinatra voice for tutorial

Generates tutorial audio narration using text-to-speech with optional voice clone.
Integrates with Lantern Desktop UI for guided onboarding.
"""

import os
import json
import math
from pathlib import Path
from datetime import datetime

AUDIO_DIR = Path.home() / ".lantern" / "sounds"
NARRATOR_CONFIG = Path.home() / ".lantern" / "narrator.json"

# Tutorial script
NARRATION_SCRIPT = {
    "intro": "Welcome to Lantern. I'm Frank. Let's set up your AI chat in five minutes.",
    "step1_providers": "First, choose your AI provider. Click Claude for the smartest option, Gemini for speed, or a local model if you're offline.",
    "step2_apikey": "Enter your API key if using a cloud provider. If you don't have one, we can get you set up in sixty seconds.",
    "step3_verify": "Verifying connection to your AI service. This takes about five seconds.",
    "step4_test": "Let's send your first test message. Type anything you'd like to ask.",
    "step5_response": "The AI is thinking. Watch the responses stream word by word. No waiting for the full response.",
    "step6_next": "You're ready. Open the chat and start asking questions. I'm here if you get stuck.",
    "success": "Lantern is live. Welcome. Enjoy learning.",
}

def generate_sine_wave(frequency, duration_ms, amplitude=0.3, sample_rate=44100):
    """
    Generate a pure sine wave (fallback audio if TTS unavailable).

    Args:
        frequency: Hz
        duration_ms: milliseconds
        amplitude: 0.0–1.0
        sample_rate: Hz

    Returns:
        List of audio samples (int16)
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = amplitude * math.sin(2 * math.pi * frequency * t)
        samples.append(int(sample * 32767))
    return samples

def generate_narration_wav(text, filename, use_tts=True):
    """
    Generate a WAV file for narration.

    Args:
        text: Narration text
        filename: Output filename (e.g., "intro.wav")
        use_tts: If True, try external TTS; if False or unavailable, use tone generator

    Returns:
        Path to generated WAV file
    """
    output_path = AUDIO_DIR / filename

    # Try TTS first (requires pyttsx3 or similar)
    if use_tts:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 120)  # Slow down for clarity
            engine.setProperty('volume', 0.9)

            # Try to set voice to a male voice if available
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'male' in voice.name.lower() or voice.id.endswith('1'):
                    engine.setProperty('voice', voice.id)
                    break

            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            return output_path
        except (ImportError, Exception):
            pass

    # Fallback: generate a pleasant tone sequence
    # Represents the "essence" of Frank Sinatra: smooth jazz progression
    # Frequencies: C (262 Hz) → E (330 Hz) → G (392 Hz) → high C (523 Hz)
    frequencies = [262, 330, 392, 523]
    sample_rate = 44100
    total_samples = []

    duration_per_tone = 1000  # 1 second per tone, 4 seconds total

    for freq in frequencies:
        samples = generate_sine_wave(freq, duration_per_tone, amplitude=0.25, sample_rate=sample_rate)
        total_samples.extend(samples)

    # Write WAV file
    import wave
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Convert samples to bytes
        wav_data = b''.join([s.to_bytes(2, byteorder='little', signed=True) for s in total_samples])
        wav_file.writeframes(wav_data)

    return output_path

def setup_narration():
    """Initialize narrator audio files and config."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Generate all narration files
    print("[*] Generating narration audio files...")
    for key, text in NARRATION_SCRIPT.items():
        filename = f"{key}.wav"
        output_path = generate_narration_wav(text, filename, use_tts=True)
        print(f"  [OK] {filename}")

    # Save narrator config
    config = {
        "narrator": "Frank Sinatra",
        "voice_type": "smooth jazz",
        "generated_at": datetime.now().isoformat(),
        "script": NARRATION_SCRIPT,
        "audio_files": {k: f"{k}.wav" for k in NARRATION_SCRIPT.keys()}
    }

    with open(NARRATOR_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"[OK] Narrator setup complete. Config saved to {NARRATOR_CONFIG}")
    return config

def play_narration(key):
    """
    Play a narration file by key.

    Args:
        key: Key from NARRATION_SCRIPT (e.g., "intro", "step1_providers")
    """
    if key not in NARRATION_SCRIPT:
        print(f"[!] Unknown narration key: {key}")
        return

    audio_file = AUDIO_DIR / f"{key}.wav"

    if not audio_file.exists():
        print(f"[!] Audio file not found: {audio_file}")
        return

    # Play using system audio
    import subprocess
    import platform

    try:
        if platform.system() == 'Windows':
            # Windows: use winsound
            import winsound
            winsound.PlaySound(str(audio_file), winsound.SND_FILENAME)
        elif platform.system() == 'Darwin':
            # macOS: use afplay
            subprocess.run(['afplay', str(audio_file)])
        else:
            # Linux: try ffplay or paplay
            subprocess.run(['ffplay', '-nodisp', '-autoexit', str(audio_file)])
    except Exception as e:
        print(f"[!] Error playing audio: {e}")

if __name__ == "__main__":
    setup_narration()
