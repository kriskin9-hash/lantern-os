@echo off
REM Launch Lantern tutorial with Frank Sinatra narration
start "" "C:\Users\alexp\Documents\gm-agent-orchestrator\lantern-tutorial-frank.html"
timeout /t 2 /nobreak
cd /d "C:\Users\alexp\Documents\gm-agent-orchestrator"
python scripts\lantern-desktop-auth-ui.py
