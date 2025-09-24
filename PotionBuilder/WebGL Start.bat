@echo off
setlocal

:: === Configuration ===
set PORT=8002
set "GAME_DIR=%~dp0"

:: Change directory to the game folder
cd /d "%GAME_DIR%"

echo Starting local server for WebGL game...
echo Serving folder: %CD%
echo Port: %PORT%

:: Start the HTTP server in background
start /B "" python -m http.server %PORT%
timeout /t 2 > nul

:: Open index.html directly
start "" http://localhost:%PORT%/index.html

echo Server running. Press Ctrl+C in the terminal to stop it.
pause
