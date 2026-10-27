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
