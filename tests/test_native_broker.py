import io
import json
import struct
import pytest

from idm_broker.broker import NativeMessageBroker


def test_native_messaging_read_and_write():
    payload = {"action": "download", "url": "https://example.com/file.zip", "output": "file.zip"}
    encoded_json = json.dumps(payload).encode("utf-8")
    header = struct.pack("<I", len(encoded_json))
    
    stream_in = io.BytesIO(header + encoded_json)
    
    broker = NativeMessageBroker()
    received_msg = broker.read_message(stream_in)
    assert received_msg == payload

    # Test writing message
    stream_out = io.BytesIO()
    response_payload = {"status": "ok", "taskId": 123}
    broker.write_message(stream_out, response_payload)
    
    stream_out.seek(0)
    raw_length = stream_out.read(4)
    length = struct.unpack("<I", raw_length)[0]
    body = stream_out.read(length)
    assert json.loads(body.decode("utf-8")) == response_payload


def test_broker_command_dispatch():
    broker = NativeMessageBroker()
    
    # Ping action
    ping_cmd = {"action": "ping"}
    res = broker.handle_command(ping_cmd)
    assert res == {"status": "ok", "message": "pong"}

    # Unknown action handling
    unknown_cmd = {"action": "invalid_command"}
    res2 = broker.handle_command(unknown_cmd)
    assert res2.get("status") == "error"
    assert "unknown action" in res2.get("error", "").lower()


def test_main_app_native_messaging_handling(monkeypatch):
    import sys
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    import main_app

    payload = {"action": "download", "url": "https://example.com/movie.mp4", "title": "movie.mp4"}
    encoded = json.dumps(payload).encode("utf-8")
    header = struct.pack("<I", len(encoded))

    fake_stdin = io.BytesIO(header + encoded)
    fake_stdout = io.BytesIO()

    class FakeBuffer:
        def __init__(self, stream):
            self._stream = stream
        def read(self, n):
            return self._stream.read(n)
        def write(self, data):
            return self._stream.write(data)
        def flush(self):
            pass

    class FakeStream:
        def __init__(self, stream):
            self.buffer = FakeBuffer(stream)

    monkeypatch.setattr(sys, "stdin", FakeStream(fake_stdin))
    monkeypatch.setattr(sys, "stdout", FakeStream(fake_stdout))

    # Mock urllib to prevent actual HTTP call
    def mock_urlopen(*args, **kwargs):
        class MockResp:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
        return MockResp()

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    with pytest.raises(SystemExit):
        main_app.handle_native_messaging()

    fake_stdout.seek(0)
    raw_len = fake_stdout.read(4)
    assert len(raw_len) == 4
    resp_len = struct.unpack("<I", raw_len)[0]
    resp_data = json.loads(fake_stdout.read(resp_len).decode("utf-8"))
    assert resp_data.get("status") == "ok"
