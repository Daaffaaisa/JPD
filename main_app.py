"""JustPressDownload (JPD) - Standalone Desktop Application Entry Point."""

import sys
import os

# Ensure src is on python path when running from source or frozen
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if os.path.exists(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from idm_gui.app import main

if __name__ == "__main__":
    if sys.platform == "win32" and not os.environ.get("PYTEST_CURRENT_TEST"):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Local\\JustPressDownload_SingleInstance_Mutex_98712"
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, "JustPressDownload (JPD)")
            if hwnd:
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
            sys.exit(0)
    main()
