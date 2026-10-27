import os
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import pytest

from idm_core.engine import DownloadEngine, DownloadResult


class NonRangeServerHandler(BaseHTTPRequestHandler):
    """Server that refuses Range requests and returns HTTP 200 with full content."""
    PAYLOAD = b"FULL_CONTENT_NO_RANGE_SUPPORT"

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.PAYLOAD)))
        self.send_header("Content-Disposition", 'attachment; filename="proper_filename.zip"')
        self.end_headers()
        self.wfile.write(self.PAYLOAD)

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def non_range_server():
    server = HTTPServer(("127.0.0.1", 0), NonRangeServerHandler)
    port = server.server_port
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{port}/api/download?id=123"
    server.shutdown()


def test_filename_extraction_from_content_disposition(non_range_server):
    engine = DownloadEngine()
    suggested_name = engine.get_filename(non_range_server)
    assert suggested_name == "proper_filename.zip"


def test_fallback_to_single_stream_when_server_returns_200_for_range(non_range_server):
    engine = DownloadEngine()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "output.bin")
        # Request 4 parts on a server that returns 200 OK
        result = engine.download(non_range_server, out_path, num_parts=4)
        
        assert result.success is True
        assert result.num_parts == 1  # Should gracefully fallback to 1 part!
        assert result.bytes_downloaded == len(NonRangeServerHandler.PAYLOAD)
        
        with open(out_path, "rb") as f:
            data = f.read()
        assert data == NonRangeServerHandler.PAYLOAD


class RateLimitedRangeServerHandler(BaseHTTPRequestHandler):
    """Server that claims Range support in HEAD, but fails Range GET with 429 if too many connections."""
    PAYLOAD = b"RATE_LIMITED_SERVER_RECOVERY_TEST_DATA" * 50
    active_range_requests = 0
    lock = threading.Lock()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.PAYLOAD)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

    def do_GET(self):
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            with self.lock:
                RateLimitedRangeServerHandler.active_range_requests += 1
                curr = RateLimitedRangeServerHandler.active_range_requests

            # If client bombards with more than 4 concurrent range connections, reject with 429!
            if curr > 4:
                with self.lock:
                    RateLimitedRangeServerHandler.active_range_requests -= 1
                self.send_response(429)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            try:
                spec = range_header.replace("bytes=", "").split("-")
                start = int(spec[0])
                end = int(spec[1]) if spec[1] else len(self.PAYLOAD) - 1
                chunk = self.PAYLOAD[start : end + 1]
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{len(self.PAYLOAD)}")
                self.send_header("Content-Length", str(len(chunk)))
                self.end_headers()
                self.wfile.write(chunk)
            finally:
                with self.lock:
                    RateLimitedRangeServerHandler.active_range_requests -= 1
        else:
            # Full stream
            self.send_response(200)
            self.send_header("Content-Length", str(len(self.PAYLOAD)))
            self.end_headers()
            self.wfile.write(self.PAYLOAD)

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def rate_limited_server():
    server = HTTPServer(("127.0.0.1", 0), RateLimitedRangeServerHandler)
    port = server.server_port
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{port}/rate_limited.zip"
    server.shutdown()


def test_fallback_when_server_rate_limits_high_concurrency(rate_limited_server):
    engine = DownloadEngine()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "rate_limited_output.bin")
        # Request 32 parts on a server that rate-limits high concurrency with 429
        result = engine.download(rate_limited_server, out_path, num_parts=32)

        # Should NOT fail or hang! Should automatically recover and succeed
        assert result.success is True
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) == len(RateLimitedRangeServerHandler.PAYLOAD)
        with open(out_path, "rb") as f:
            data = f.read()
        assert data == RateLimitedRangeServerHandler.PAYLOAD

