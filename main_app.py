"""JustPressDownload (JPD) - Standalone Desktop Application Entry Point."""

import sys
import os
import struct
import json
import subprocess
import urllib.request

# Guarantee working directory is always the application folder (vital when started at boot or by browser)
if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(app_dir):
    try:
        os.chdir(app_dir)
    except Exception:
        pass

# Ensure src is on python path when running from source or frozen
src_dir = os.path.join(app_dir, "src")
if os.path.exists(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Enable Per-Monitor V2 High-DPI Awareness on Windows so fonts, icons, and borders render razor-sharp in HD (no blur)
if sys.platform == "win32":
    import ctypes
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

from idm_gui.app import main


def handle_native_messaging():
    """Handles Chrome/Edge/Firefox Native Messaging host invocations."""
    try:
        raw_len = sys.stdin.buffer.read(4)
        if len(raw_len) < 4:
            return
        msg_len = struct.unpack("<I", raw_len)[0]
        payload = json.loads(sys.stdin.buffer.read(msg_len).decode("utf-8"))
    except Exception:
        return

    # Immediately write success response to browser
    try:
        resp = json.dumps({"status": "ok", "message": "Dispatched to JPD"}).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("<I", len(resp)))
        sys.stdout.buffer.write(resp)
        sys.stdout.buffer.flush()
    except Exception:
        pass

    # Forward to running JPD instance or launch it
    dispatched = False
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:19900/api/download",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=1.0) as r:
            if r.status == 200:
                dispatched = True
    except Exception:
        dispatched = False

    if not dispatched:
        # App is closed: launch JustPressDownload desktop GUI with the download URL
        exe_path = sys.executable if getattr(sys, "frozen", False) else os.path.join(app_dir, "JustPressDownload.exe")
        if not os.path.exists(exe_path):
            cmd = [sys.executable, os.path.abspath(__file__)]
        else:
            cmd = [exe_path]

        if payload.get("url"):
            cmd.extend(["--url", payload["url"]])
        if payload.get("title"):
            cmd.extend(["--title", payload["title"]])
        if payload.get("referer"):
            cmd.extend(["--referer", payload["referer"]])

        DETACHED = 0x00000008 if sys.platform == "win32" else 0
        try:
            subprocess.Popen(cmd, cwd=app_dir, creationflags=DETACHED)
        except Exception:
            pass

    sys.exit(0)


if __name__ == "__main__":
    # Check if launched via custom protocol scheme: justpressdownload://download?url=...
    if len(sys.argv) > 1 and sys.argv[1].startswith("justpressdownload://"):
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(sys.argv[1])
            params = urllib.parse.parse_qs(parsed.query)
            target_url = params.get("url", [""])[0]
            target_title = params.get("title", [""])[0]
            target_referer = params.get("referer", [""])[0]
            sys.argv = [sys.argv[0], "--url", target_url, "--title", target_title, "--referer", target_referer]
        except Exception:
            pass

    # Check if launched by browser Native Messaging (e.g. chrome-extension://...)
    if len(sys.argv) > 1 and ("chrome-extension://" in sys.argv[1] or sys.argv[1].endswith(".json")):
        handle_native_messaging()

    if sys.platform == "win32" and not os.environ.get("PYTEST_CURRENT_TEST"):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Local\\JustPressDownload_SingleInstance_Mutex_98712"
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            # If another instance is running and we were passed a download URL, forward it
            if "--url" in sys.argv:
                try:
                    u_idx = sys.argv.index("--url")
                    u_val = sys.argv[u_idx + 1] if u_idx + 1 < len(sys.argv) else ""
                    t_val = ""
                    r_val = ""
                    if "--title" in sys.argv:
                        t_idx = sys.argv.index("--title")
                        t_val = sys.argv[t_idx + 1] if t_idx + 1 < len(sys.argv) else ""
                    if "--referer" in sys.argv:
                        r_idx = sys.argv.index("--referer")
                        r_val = sys.argv[r_idx + 1] if r_idx + 1 < len(sys.argv) else ""
                    req = urllib.request.Request(
                        "http://127.0.0.1:19900/api/download",
                        data=json.dumps({"url": u_val, "title": t_val, "referer": r_val}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    urllib.request.urlopen(req, timeout=1.0)
                except Exception:
                    pass
                # Kept minimized in tray, only the download dialog is opened by the running instance
                sys.exit(0)

            # Manual double-click launch: restore main dashboard window
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, "Just Press Download")
            if not hwnd:
                hwnd = user32.FindWindowW(None, "JustPressDownload (JPD)")
            if hwnd:
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
            sys.exit(0)
    main()
