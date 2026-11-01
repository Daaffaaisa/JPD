@echo off
title Build IDM Clone Standalone EXE
cd /d "%~dp0"
echo =======================================================
echo Building IDM Clone Standalone Windows Executable (.exe)
echo =======================================================
echo.
uv run pyinstaller --noconsole --onefile --name "IDMClone" --icon "icon.ico" --add-data "icon.ico;." --add-data "icon.png;." --paths "src" --hidden-import "PIL" --hidden-import "PIL.ImageTk" --hidden-import "requests" --hidden-import "yt_dlp" main_app.py
if %ERRORLEVEL% EQU 0 (
    copy /Y "dist\IDMClone.exe" "IDMClone.exe" >nul
    echo.
    echo =======================================================
    echo SUCCESS: IDMClone.exe created in project root and dist/
    echo =======================================================
) else (
    echo.
    echo [ERROR] Build failed.
)
pause
