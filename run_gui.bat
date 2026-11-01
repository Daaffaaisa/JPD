@echo off
title IDM Clone Desktop App
cd /d "%~dp0"

if exist "IDMClone.exe" (
    start "" "IDMClone.exe"
    exit /b 0
)

echo Starting IDM Clone GUI...
uv run idm-gui
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to start IDM Clone GUI.
    pause
)
