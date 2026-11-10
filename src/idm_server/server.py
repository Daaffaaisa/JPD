import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Optional
import urllib.parse

from idm_scheduler.queue import DownloadQueue


class LocalServerHandler(BaseHTTPRequestHandler):
    queue: Optional[DownloadQueue] = None
    on_task_added: Optional[Callable[[str, dict], None]] = None

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Access-Control-Request-Private-Network")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            lang = "id"
            try:
                from idm_gui.settings import settings
                lang = settings.get_language()
            except Exception:
                pass
            data = {
                "status": "ok",
                "app": "Just Press Download (IDM Integration)",
                "version": "2.0.0",
                "language": lang,
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path == "/api/status":
            query = urllib.parse.parse_qs(parsed.query)
            task_id = query.get("taskId", [""])[0]
            if self.queue and task_id:
                task = self.queue.get_task(task_id)
                if task:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    data = {
                        "status": "ok",
                        "task": {
                            "id": task.task_id,
                            "url": task.url,
                            "status": task.status.value,
                            "bytesDownloaded": task.bytes_downloaded,
                            "totalBytes": task.total_bytes,
                            "error": task.error,
                        },
                    }
                    self.wfile.write(json.dumps(data).encode("utf-8"))
                    return

            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Task not found"}).encode("utf-8"))
            return

        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/download":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            url = payload.get("url")
            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Missing url"}).encode("utf-8"))
                return

            # Determine destination path
            title = payload.get("title") or "download.bin"
            folder = payload.get("folder") or os.path.join(os.path.expanduser("~"), "Downloads")
            out_path = os.path.join(folder, title)

            task_id = "unknown"
            if self.queue:
                task_id = self.queue.add_task(url=url, output_path=out_path)

            if self.on_task_added:
                try:
                    self.on_task_added(task_id, payload)
                except Exception:
                    pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "taskId": task_id}).encode("utf-8"))
            return

        if path == "/api/settings":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}
            if "language" in payload:
                new_lang = payload["language"]
                try:
                    from idm_gui.settings import settings
                    settings.set_language(new_lang)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return

        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()

    def log_message(self, format, *args):
        pass


class LocalDownloadServer:
    """Lightweight loopback server on 127.0.0.1 for browser extension IPC."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 19900,
        queue: Optional[DownloadQueue] = None,
        on_task_added: Optional[Callable[[str, dict], None]] = None,
    ):
        self.host = host
        self.port = port
        self.queue = queue
        self.on_task_added = on_task_added
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self):
        class Handler(LocalServerHandler):
            queue = self.queue
            on_task_added = self.on_task_added

        # Try designated port, or if in use, pick an available port
        try:
            self.server = HTTPServer((self.host, self.port), Handler)
        except OSError:
            # Fallback to dynamic port if 1001 is busy
            self.server = HTTPServer((self.host, 0), Handler)
            
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
