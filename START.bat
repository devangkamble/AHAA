@echo off
title AHAA Server
color 0A
echo.
echo ================================================
echo   AHAA - Adaptive Health Advisor Agent
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ERROR: Python is not installed or not in PATH
    echo.
    echo   Please download Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: During install, check the box:
    echo   "Add Python to PATH"
    echo.
    pause
    exit
)

echo   Python found!
echo.

REM Check if server.py exists in same folder
if not exist "%~dp0server.py" (
    echo   ERROR: server.py not found!
    echo   Make sure server.py is in the same folder as START.bat
    echo.
    pause
    exit
)

REM Check if index.html exists in same folder  
if not exist "%~dp0index.html" (
    echo   ERROR: index.html not found!
    echo   Make sure index.html is in the same folder as START.bat
    echo.
    pause
    exit
)

echo   Starting AHAA server...
echo.
echo   When you see the server is ready:
echo   Open Chrome and go to: http://localhost:8000
echo.
echo   Keep this window open while using AHAA!
echo   Close this window to stop the server.
echo.
echo ================================================
echo.

REM Change to the folder containing this bat file
cd /d "%~dp0"

REM Start the server
python server.py

echo.
echo   Server stopped.
pause
