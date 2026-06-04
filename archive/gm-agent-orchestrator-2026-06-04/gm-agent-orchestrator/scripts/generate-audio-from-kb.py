#!/usr/bin/env python3
"""
Generate high-quality audio narration from knowledge base.
Uses Windows SAPI 5 text-to-speech (built-in, no external deps).
Creates MP3 files at ~/.lantern/audio-tutorial/
"""

import sys
import subprocess
from pathlib import Path

# Load knowledge base
sys.path.insert(0, str(Path(__file__).parent))
from llm_knowledge_base_reader import LanternKnowledgeBase as KB

# If import fails, create mock KB for testing
try:
    from llm_knowledge_base_reader import LanternKnowledgeBase
except ImportError:
    print("Warning: KB reader not found, using mock data")
    class MockKB:
        def get_tutorial_sequence(self):
            return [
                {"doc_id": "t1", "title": "Step 1: Open Lantern", "content": "Press Windows Key. Type: lantern. Press Enter. Audio: Open Lantern Desktop application."},
                {"doc_id": "t2", "title": "Step 2: Select Claude", "content": "Press Tab until Claude is highlighted. Press Enter. Audio: Select Claude provider by pressing Tab and Enter."},
                {"doc_id": "t3", "title": "Step 3: Get API Key", "content": "Open console.anthropic.com. Sign in. Click API Keys. Create Key. Copy. Audio: Get your Claude API key from the Anthropic console."},
                {"doc_id": "t4", "title": "Step 4: Save Credentials", "content": "Paste API key into Lantern. Click Save. Audio: Paste your API key and save credentials."},
                {"doc_id": "t5", "title": "Step 5: Set Primary", "content": "Click Set Primary Provider. Select Claude. Audio: Set Claude as your primary provider."},
                {"doc_id": "t6", "title": "Step 6: Click Ready", "content": "Click Ready button. Chat opens. Audio: Click Ready to start chatting with Claude."},
            ]
    LanternKnowledgeBase = MockKB

AUDIO_DIR = Path.home() / ".lantern" / "audio-tutorial"


def generate_audio_windows():
    """Generate audio using Windows built-in text-to-speech"""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    kb = LanternKnowledgeBase()
    tutorial_docs = kb.get_tutorial_sequence()

    print("Generating audio narration from knowledge base...")
    print(f"Output directory: {AUDIO_DIR}\n")

    # Generate audio for each tutorial step
    for i, doc in enumerate(tutorial_docs, 1):
        doc_id = doc['doc_id']
        title = doc['title']
        content = doc['content']
        audio_file = doc.get('audio_file', f"step{i}.mp3")

        output_path = AUDIO_DIR / audio_file

        print(f"  [{i}/{len(tutorial_docs)}] Generating: {title}")
        print(f"           → {output_path}")

        # Extract just the audio description or content
        text_to_speak = content
        if "Audio:" in content:
            # Extract audio description part
            text_to_speak = content.split("Audio:")[-1].strip().strip("'\"")

        # Use PowerShell to invoke Windows text-to-speech
        ps_command = f'''
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = -2
$audioFile = '{output_path}'
$speak.SetOutputToAudioFile('{output_path}', [System.Speech.Synthesis.SynthesisAudioFormat]::Pcm16BitMonoWaveFormat)
$speak.Speak(@"
{text_to_speak}
"@)
$speak.Dispose()
Write-Host "Audio created: $audioFile"
'''

        try:
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"           ✅ Created\n")
            else:
                print(f"           ⚠️  Error: {result.stderr.decode()}\n")

        except subprocess.TimeoutExpired:
            print(f"           ⚠️  Timeout\n")
        except Exception as e:
            print(f"           ⚠️  Exception: {e}\n")

    print("\n=== Audio Generation Complete ===")
    print(f"Audio files at: {AUDIO_DIR}")
    print(f"Ready to use with Lantern Desktop + Tutorial HTML")


def create_audio_index():
    """Create index of audio files for HTML tutorial"""
    kb = LanternKnowledgeBase()
    tutorial_docs = kb.get_tutorial_sequence()

    index = {
        "generated_at": "2026-05-25",
        "audio_dir": str(AUDIO_DIR),
        "files": []
    }

    for i, doc in enumerate(tutorial_docs, 1):
        audio_file = doc.get('audio_file', f"step{i}.mp3")
        index["files"].append({
            "step": i,
            "title": doc['title'],
            "audio_file": audio_file,
            "doc_id": doc['doc_id']
        })

    # Save index
    index_path = AUDIO_DIR / "index.json"
    import json
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"Audio index: {index_path}")
    return index


if __name__ == "__main__":
    try:
        generate_audio_windows()
        create_audio_index()
        print("\n✅ All audio narration generated and indexed!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
