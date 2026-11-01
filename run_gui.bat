@echo off
title JustPressDownload (JPD) Desktop App
cd /d "%~dp0"

if exist "JustPressDownload.exe" (
    start "" "JustPressDownload.exe"
    exit /b 0
)

echo Starting JustPressDownload (JPD) GUI...
uv run idm-gui
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to start JustPressDownload (JPD) GUI.
    pause
)
