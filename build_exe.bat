@echo off
title Build JustPressDownload (JPD) Standalone EXE
cd /d "%~dp0"
echo =================================================================
echo Building JustPressDownload (JPD) Standalone Windows Executable (.exe)
echo =================================================================
echo.
uv run pyinstaller --noconsole --onefile --runtime-tmpdir _app_cache --name "JustPressDownload" --icon "icon.ico" --add-data "icon.ico;." --add-data "icon.png;." --paths "src" --hidden-import "PIL" --hidden-import "PIL.ImageTk" --hidden-import "requests" --hidden-import "yt_dlp" --hidden-import "pystray" --hidden-import "pystray._win32" main_app.py
uv run pyinstaller --onefile --runtime-tmpdir _app_cache --name "JustPressDownloadHost" --icon "icon.ico" host_app.py
if %ERRORLEVEL% EQU 0 (
    copy /Y "dist\JustPressDownload.exe" "JustPressDownload.exe" >nul
    copy /Y "dist\JustPressDownloadHost.exe" "JustPressDownloadHost.exe" >nul
    echo.
    echo =================================================================
    echo SUCCESS: JustPressDownload.exe & JustPressDownloadHost.exe created
    echo =================================================================
) else (
    echo.
    echo [ERROR] Build failed.
)
pause
