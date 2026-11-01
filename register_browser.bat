@echo off
title JustPressDownload (JPD) - Integrasi Browser
cd /d "%~dp0"
echo ==================================================================
echo   Mendaftarkan Integrasi Browser JustPressDownload (JPD)...
echo ==================================================================
echo.
uv run python scripts/register_extension.py
echo.
pause
