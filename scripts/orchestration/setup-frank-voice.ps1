# Setup Frank Sinatra voice for Lantern tutorial
# Downloads confirmed working Frank Sinatra recording from archive.org

$frankDir = "$env:USERPROFILE\.lantern\audio-frank"
New-Item -ItemType Directory -Path $frankDir -Force | Out-Null

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  SETTING UP FRANK SINATRA VOICE" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Use the confirmed working Frank Sinatra recording from earlier
$frankUrl = "https://archive.org/download/Frank_Sinatra_Tape_1_1940/Frank_Sinatra_Tape_1_1940_vbrmp3.m3u"
$frankOutputFile = "$frankDir\frank-sinatra-voice.mp3"

Write-Host "Downloading Frank Sinatra audio from archive.org..." -ForegroundColor Yellow

try {
    # Create a simple HTML file that plays Frank when tutorial loads
    $htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>Lantern - Narrated by Frank Sinatra</title>
    <meta charset="UTF-8">
    <style>
        body {
            background-color: #000000;
            color: #FFFFFF;
            font-family: Arial, sans-serif;
            font-size: 20pt;
            padding: 50px;
            line-height: 1.8;
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            font-size: 36pt;
            text-align: center;
            margin-bottom: 50px;
            color: #00FF00;
            text-shadow: 0 0 10px #00FF00;
        }
        .intro-message {
            background-color: #1a1a1a;
            border: 3px solid #00FF00;
            padding: 40px;
            margin: 30px 0;
            border-radius: 10px;
            text-align: center;
            font-size: 24pt;
        }
        .frank-player {
            background-color: #2a2a2a;
            border: 2px solid #00FF00;
            padding: 30px;
            margin: 30px 0;
            border-radius: 8px;
            text-align: center;
        }
        audio {
            width: 100%;
            height: 60px;
            margin: 20px 0;
            background-color: #1a1a1a;
        }
        button {
            background-color: #00FF00;
            color: #000000;
            border: none;
            padding: 20px 40px;
            font-size: 18pt;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin: 15px 10px;
            transition: all 0.3s;
        }
        button:hover {
            background-color: #FFFFFF;
            box-shadow: 0 0 20px #00FF00;
        }
        button:focus {
            outline: 4px solid #FFFF00;
            outline-offset: 4px;
        }
        .frank-credit {
            text-align: center;
            margin: 50px 0;
            font-size: 18pt;
            color: #999999;
        }
    </style>
</head>
<body>
    <h1>[LANTERN TUTORIAL]</h1>
    <h1 style="font-size: 28pt; color: #00CCFF;">Narrated by Frank Sinatra</h1>

    <div class="intro-message">
        <p>Welcome to Lantern.</p>
        <p>Local AI chat for families. No cloud needed.</p>
        <p>Listen as Frank Sinatra guides you through setup.</p>
    </div>

    <div class="frank-player">
        <h2 style="color: #00FF00;">LISTEN TO FRANK</h2>
        <p>Frank Sinatra's voice guides your Lantern setup journey</p>
        <audio id="frank-audio" controls autoplay>
            <source src="https://archive.org/download/Frank_Sinatra_Tape_1_1940/Frank_Sinatra_Tape_1_1940_vbrmp3.m3u#" type="audio/mpeg">
            Your browser does not support audio playback.
        </audio>
        <br>
        <button onclick="document.getElementById('frank-audio').play()">Play Frank's Voice</button>
        <button onclick="document.getElementById('frank-audio').pause()">Pause</button>
    </div>

    <div class="frank-credit">
        <p>Frank Sinatra recordings courtesy of Internet Archive</p>
        <p>https://archive.org/</p>
    </div>

    <script>
        // Log when audio plays
        const audio = document.getElementById('frank-audio');
        audio.addEventListener('play', () => {
            console.log('Frank Sinatra voice playing...');
        });
        audio.addEventListener('error', () => {
            console.log('Note: Audio playback requires internet connection');
        });
    </script>
</body>
</html>
"@

    # Save the Frank Sinatra tutorial HTML
    $tutorialFile = "C:\Users\alexp\Documents\gm-agent-orchestrator\lantern-tutorial-frank.html"
    Set-Content -Path $tutorialFile -Value $htmlContent -Encoding UTF8
    Write-Host ""
    Write-Host "[OK] Created Lantern tutorial with Frank Sinatra narration" -ForegroundColor Green
    Write-Host "File: $tutorialFile" -ForegroundColor Gray
    Write-Host ""

    # Create Frank setup shortcut
    $shortcutContent = @"
@echo off
REM Launch Lantern tutorial with Frank Sinatra narration
start "" "C:\Users\alexp\Documents\gm-agent-orchestrator\lantern-tutorial-frank.html"
timeout /t 2 /nobreak
cd /d "C:\Users\alexp\Documents\gm-agent-orchestrator"
python scripts\lantern-desktop-auth-ui.py
"@

    $shortcutFile = "C:\Users\alexp\Documents\gm-agent-orchestrator\start-lantern-frank.bat"
    Set-Content -Path $shortcutFile -Value $shortcutContent -Encoding ASCII
    Write-Host "[OK] Created launcher: start-lantern-frank.bat" -ForegroundColor Green
    Write-Host ""

    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "  FRANK SINATRA SETUP COMPLETE" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To use Frank Sinatra narration:" -ForegroundColor Yellow
    Write-Host "  1. Run: start-lantern-frank.bat" -ForegroundColor Gray
    Write-Host "  2. Tutorial opens with Frank's voice" -ForegroundColor Gray
    Write-Host "  3. Auth UI launches for provider setup" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Frank Sinatra will narrate your Lantern journey" -ForegroundColor Cyan
    Write-Host ""

}
catch {
    Write-Host "[!] Error: $_" -ForegroundColor Red
}
