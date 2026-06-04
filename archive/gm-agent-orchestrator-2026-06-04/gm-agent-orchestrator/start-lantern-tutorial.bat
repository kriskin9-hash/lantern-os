@echo off
REM Lantern Desktop Accessible Tutorial Launcher
REM Opens HTML tutorial + launches Lantern Desktop auth UI

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================
echo   LANTERN DESKTOP - ACCESSIBLE TUTORIAL
echo ============================================
echo.
echo Opening tutorial in your browser...
echo.

REM Verify lantern-tutorial.html exists
if not exist "lantern-tutorial.html" (
    echo ERROR: lantern-tutorial.html not found in %CD%
    echo Expected location: %CD%\lantern-tutorial.html
    pause
    exit /b 1
)

REM Open HTML tutorial in default browser (use full path)
start "" "%CD%\lantern-tutorial.html"

REM Wait 3 seconds, then launch Lantern Desktop auth UI
timeout /t 3 /nobreak

echo.
echo Launching Lantern Desktop authentication...
echo.

REM Verify Python script exists
if not exist "scripts\lantern-desktop-auth-ui.py" (
    echo ERROR: lantern-desktop-auth-ui.py not found
    echo Expected location: %CD%\scripts\lantern-desktop-auth-ui.py
    pause
    exit /b 1
)

REM Launch the Python auth UI
python "%CD%\scripts\lantern-desktop-auth-ui.py"

echo.
echo If you see this message, setup is complete!
echo.
pause
