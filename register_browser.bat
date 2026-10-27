@echo off
title IDM Clone - Register Browser Integration
cd /d "%~dp0"
echo Registering IDM Clone Native Messaging Host for Chrome, Edge, and Firefox...
uv run python scripts/register_extension.py
echo.
pause
