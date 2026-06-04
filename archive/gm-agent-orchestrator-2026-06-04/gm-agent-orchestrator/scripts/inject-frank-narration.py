#!/usr/bin/env python3
"""
Inject Frank Sinatra narration into Lantern tutorial.
Replaces generic TTS with Sinatra audio from internet archive.
"""

import os
import json
from pathlib import Path
import urllib.request

TUTORIAL_HTML = Path.home() / "Documents" / "gm-agent-orchestrator" / "lantern-tutorial.html"
FRANK_DIR = Path.home() / ".lantern" / "audio-frank"
FRANK_DIR.mkdir(parents=True, exist_ok=True)

# Frank Sinatra recordings from internet archive
SINATRA_SOURCES = {
    "intro": "https://archive.org/download/Frank_Sinatra_Tape_1_1940/Frank_Sinatra_Tape_1_1940_vbrmp3.m3u",
    "step1": "https://archive.org/download/Frank_Sinatra_Tape_2_1940/Frank_Sinatra_Tape_2_1940_vbrmp3.m3u",
    "step2": "https://archive.org/download/Frank_Sinatra_Tape_3_1940/Frank_Sinatra_Tape_3_1940_vbrmp3.m3u",
    "step3": "https://archive.org/download/Frank_Sinatra_Tape_4_1940/Frank_Sinatra_Tape_4_1940_vbrmp3.m3u",
    "step4": "https://archive.org/download/Frank_Sinatra_Tape_5_1940/Frank_Sinatra_Tape_5_1940_vbrmp3.m3u",
    "step5": "https://archive.org/download/Frank_Sinatra_Tape_6_1940/Frank_Sinatra_Tape_6_1940_vbrmp3.m3u",
    "step6": "https://archive.org/download/Frank_Sinatra_Tape_1_1945/Frank_Sinatra_Tape_1_1945_vbrmp3.m3u",
    "success": "https://archive.org/download/Frank_Sinatra_Tape_1_1950/Frank_Sinatra_Tape_1_1950_vbrmp3.m3u",
}

def download_frank_audio():
    """Download Frank Sinatra audio from internet archive"""
    print("Downloading Frank Sinatra narration from archive.org...")
    print("=" * 70)

    frank_index = {}

    for step_name, m3u_url in SINATRA_SOURCES.items():
        print(f"\n[{step_name.upper()}]")
        print(f"  Source: {m3u_url}")

        try:
            # Fetch M3U playlist
            with urllib.request.urlopen(m3u_url, timeout=10) as response:
                m3u_content = response.read().decode('utf-8')

            # Extract MP3 URL from M3U playlist
            mp3_lines = [line.strip() for line in m3u_content.split('\n')
                        if line.strip().endswith('.mp3')]

            if not mp3_lines:
                print(f"  [!] No MP3 found in playlist")
                continue

            mp3_url = mp3_lines[0]
            print(f"  Found MP3: {mp3_url}")

            # Download MP3
            output_file = FRANK_DIR / f"frank-{step_name}.mp3"
            print(f"  Downloading to {output_file.name}...")

            urllib.request.urlretrieve(mp3_url, output_file)
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"  [OK] Downloaded ({file_size_mb:.1f} MB)")

            frank_index[step_name] = str(output_file)

        except Exception as e:
            print(f"  [!] Error: {e}")

    # Save index
    index_file = FRANK_DIR / "frank-narration-index.json"
    with open(index_file, 'w') as f:
        json.dump(frank_index, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Frank Sinatra narration downloaded to: {FRANK_DIR}")
    print(f"Index saved to: {index_file}")
    print("\nFrank Sinatra narration ready for tutorial!")

    return frank_index

def create_frank_tutorial_html():
    """Create tutorial HTML with Frank Sinatra audio buttons"""

    frank_index = json.loads(open(FRANK_DIR / "frank-narration-index.json").read())

    frank_html = """
    <html>
    <head>
        <title>Lantern Tutorial - Narrated by Frank Sinatra</title>
        <style>
            body {
                background-color: #000000;
                color: #FFFFFF;
                font-family: Arial, sans-serif;
                font-size: 18pt;
                padding: 40px;
                line-height: 1.6;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            h1 {
                font-size: 32pt;
                text-align: center;
                margin-bottom: 40px;
            }
            .step {
                background-color: #1a1a1a;
                border: 2px solid #FFFFFF;
                padding: 30px;
                margin: 30px 0;
                border-radius: 10px;
            }
            .step h2 {
                font-size: 24pt;
                margin-bottom: 20px;
                color: #00FF00;
            }
            .step p {
                font-size: 18pt;
                margin: 15px 0;
            }
            .frank-button {
                background-color: #003300;
                color: #00FF00;
                border: 3px solid #00FF00;
                padding: 15px 30px;
                font-size: 16pt;
                border-radius: 8px;
                cursor: pointer;
                margin: 20px 0;
                font-weight: bold;
                transition: all 0.3s;
            }
            .frank-button:hover {
                background-color: #00FF00;
                color: #000000;
                box-shadow: 0 0 20px #00FF00;
            }
            .frank-button:focus {
                outline: 4px solid #FFFF00;
                outline-offset: 2px;
            }
            audio {
                width: 100%;
                margin: 15px 0;
                background-color: #000;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>[🎤 LANTERN TUTORIAL 🎤]<br>Narrated by Frank Sinatra</h1>
"""

    steps = [
        ("intro", "Welcome to Lanterns", "Local AI chat for families. No cloud needed."),
        ("step1", "Step 1: Open Lantern Desktop", "Press the Windows key and type LANTERN"),
        ("step2", "Step 2: Select Claude", "Use Tab to navigate, press Enter to select"),
        ("step3", "Step 3: Get Your API Key", "Visit console.anthropic.com to get your key"),
        ("step4", "Step 4: Paste Your API Key", "Press Tab to move to the API key field"),
        ("step5", "Step 5: Set Claude as Primary", "Select Claude as your primary provider"),
        ("step6", "Step 6: Click Ready", "Press Enter to start chatting with Claude"),
        ("success", "Congratulations!", "You're now ready to use Lantern with Claude"),
    ]

    for step_key, title, description in steps:
        audio_file = frank_index.get(step_key)

        frank_html += f"""
            <div class="step">
                <h2>{title}</h2>
                <p>{description}</p>
"""

        if audio_file:
            frank_html += f"""
                <button class="frank-button" onclick="playAudio('{audio_file}')">
                    [🎤 HEAR FRANK'S VOICE]
                </button>
                <audio id="audio-{step_key}" controls style="margin: 15px 0;">
                    <source src="file:///{audio_file}" type="audio/mpeg">
                    Your browser does not support audio playback.
                </audio>
"""
        else:
            frank_html += f"""
                <p style="color: #FF6600;">[Audio not available for this step]</p>
"""

        frank_html += """
            </div>
"""

    frank_html += """
        </div>
        <script>
            function playAudio(audioFile) {
                const audio = new Audio('file:///' + audioFile);
                audio.play();
            }
        </script>
    </body>
    </html>
"""

    output_file = Path.home() / "Documents" / "gm-agent-orchestrator" / "lantern-tutorial-frank.html"
    with open(output_file, 'w') as f:
        f.write(frank_html)

    print(f"\n[OK] Created Franks Sinatra tutorial: {output_file}")
    return output_file

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LANTERN - FRANK SINATRA NARRATION INJECTOR")
    print("=" * 70)

    try:
        frank_index = download_frank_audio()
        if frank_index:
            html_file = create_frank_tutorial_html()
            print(f"\n[OK] Frank Sinatra tutorial ready!")
            print(f"Open: {html_file}")
        else:
            print("\n[!] Could not download Frank Sinatra audio")
    except Exception as e:
        print(f"\n[!] Error: {e}")
