@echo off
title Build JustPressDownload (JPD) Standalone EXE
cd /d "%~dp0"
echo =================================================================
echo Building JustPressDownload (JPD) Standalone Windows Executable (.exe)
echo =================================================================
echo.

taskkill /F /IM "JustPressDownload.exe" >nul 2>&1
taskkill /F /IM "Just Press Download.exe" >nul 2>&1

uv run pyinstaller -y --noconsole --onedir --manifest "app.manifest" --name "JustPressDownload" --icon "icon.ico" --add-data "icon.ico;." --add-data "icon.png;." --paths "src" --hidden-import "PIL" --hidden-import "PIL.ImageTk" --hidden-import "requests" --hidden-import "yt_dlp" --hidden-import "pystray" --hidden-import "pystray._win32" main_app.py
uv run pyinstaller -y --onedir --manifest "app.manifest" --name "JustPressDownloadHost" --icon "icon.ico" host_app.py
if %ERRORLEVEL% EQU 0 (
    robocopy "dist\JustPressDownload\_internal" "_internal" /E /NFL /NDL /NJH /NJS /nc /ns /np >nul
    copy /Y "dist\JustPressDownload\JustPressDownload.exe" "Just Press Download.exe" >nul
    copy /Y "dist\JustPressDownload\JustPressDownload.exe" "JustPressDownload.exe" >nul
    copy /Y "dist\JustPressDownload\JustPressDownload.exe" "dist\JustPressDownload\Just Press Download.exe" >nul
    copy /Y "dist\JustPressDownloadHost\JustPressDownloadHost.exe" "JustPressDownloadHost.exe" >nul
    copy /Y "icon.ico" "dist\JustPressDownload\icon.ico" >nul
    copy /Y "icon.png" "dist\JustPressDownload\icon.png" >nul
    copy /Y "icon.ico" "dist\JustPressDownload\_internal\icon.ico" >nul
    copy /Y "icon.png" "dist\JustPressDownload\_internal\icon.png" >nul
    copy /Y "icon.ico" "_internal\icon.ico" >nul
    copy /Y "icon.png" "_internal\icon.png" >nul
    echo.
    echo =================================================================
    echo SUCCESS: "Just Press Download.exe" & JustPressDownloadHost.exe created (ONEDIR INSTANT LAUNCH, HIGH-DPI AWARE)
    echo =================================================================
) else (
    echo.
    echo [ERROR] Build failed.
)
pause
