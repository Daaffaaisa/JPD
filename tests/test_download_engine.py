import os
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import pytest

from idm_core.engine import DownloadEngine, DownloadResult


class MockRangeHTTPHandler(BaseHTTPRequestHandler):
    """Mock HTTP server that supports HTTP Range requests (RFC 7233)."""
    TEST_PAYLOAD = b"Hello, IDM Clone! This is a test file for segmented multipart download." * 200

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.TEST_PAYLOAD)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Type", "application/octet-stream")
        self.end_headers()

    def do_GET(self):
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            byte_range = range_header.split("=")[1]
            start_str, end_str = byte_range.split("-")
            start = int(start_str)
            end = int(end_str) if end_str else len(self.TEST_PAYLOAD) - 1
            if end >= len(self.TEST_PAYLOAD):
                end = len(self.TEST_PAYLOAD) - 1

            chunk = self.TEST_PAYLOAD[start : end + 1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(self.TEST_PAYLOAD)}")
            self.send_header("Content-Length", str(len(chunk)))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            self.wfile.write(chunk)
        else:
            self.send_response(200)
            self.send_header("Content-Length", str(len(self.TEST_PAYLOAD)))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            self.wfile.write(self.TEST_PAYLOAD)

    def log_message(self, format, *args):
        pass  # Suppress logging in test runner


@pytest.fixture(scope="module")
def mock_server():
    server = HTTPServer(("127.0.0.1", 0), MockRangeHTTPHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/testfile.dat", MockRangeHTTPHandler.TEST_PAYLOAD
    server.shutdown()


def test_segmented_download_with_range_support(mock_server):
    url, expected_data = mock_server
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "downloaded.dat")
        engine = DownloadEngine()
        
        result: DownloadResult = engine.download(url, out_path, num_parts=4)
        
        assert result.success is True
        assert result.bytes_downloaded == len(expected_data)
        assert result.num_parts == 4
        assert os.path.exists(out_path)
        with open(out_path, "rb") as f:
            assert f.read() == expected_data
