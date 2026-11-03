"""JustPressDownload (JPD) - Dedicated Browser Native Messaging Host.

Console subsystem executable connected to Chrome/Edge/Firefox stdio pipe.
Reads length-prefixed JSON from browser and forwards to JustPressDownload GUI,
launching the GUI process automatically if the app is closed.
"""

import json
import os
import struct
import subprocess
import sys
import urllib.request


def main():
    # Read length-prefixed JSON from browser
    payload = None
    try:
        raw_len = sys.stdin.buffer.read(4)
        if len(raw_len) == 4:
            msg_len = struct.unpack("<I", raw_len)[0]
            raw_body = sys.stdin.buffer.read(msg_len)
            payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        pass

    # Immediately reply to browser so Chrome/Edge closes pipe happily
    try:
        resp = json.dumps({"status": "ok", "message": "Host received payload"}).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("<I", len(resp)))
        sys.stdout.buffer.write(resp)
        sys.stdout.buffer.flush()
    except Exception:
        pass

    if not payload:
        sys.exit(0)

    # Resolve application directory and target GUI binary
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    gui_exe = os.path.join(base_dir, "JustPressDownload.exe")

    # 1. Fast socket check: if JustPressDownload is already running, port 19900 will answer in 1ms
    dispatched = False
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.04)
        s.connect(("127.0.0.1", 19900))
        # Port is open! Send HTTP request
        s.settimeout(1.0)
        body = json.dumps(payload).encode("utf-8")
        http_data = (
            f"POST /api/download HTTP/1.1\r\n"
            f"Host: 127.0.0.1:19900\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n\r\n"
        ).encode("utf-8") + body
        s.sendall(http_data)
        s.close()
        dispatched = True
    except Exception:
        dispatched = False

    # 2. If app is completely closed: launch JustPressDownload.exe directly!
    if not dispatched:
        cmd = [gui_exe]
        if payload.get("url"):
            cmd.extend(["--url", payload["url"]])
        if payload.get("title"):
            cmd.extend(["--title", payload["title"]])
        if payload.get("referer"):
            cmd.extend(["--referer", payload["referer"]])

        DETACHED = 0x00000008 if sys.platform == "win32" else 0
        try:
            subprocess.Popen(cmd, cwd=base_dir, creationflags=DETACHED)
        except Exception as e:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
