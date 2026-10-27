import json
import struct
import sys
from typing import Any, BinaryIO, Optional


class NativeMessageBroker:
    """Handles Chrome/Firefox Native Messaging protocol (length-prefixed JSON stdio)."""

    def read_message(self, stream: Optional[BinaryIO] = None) -> Optional[dict[str, Any]]:
        source = stream or sys.stdin.buffer
        raw_length = source.read(4)
        if len(raw_length) < 4:
            return None
        message_length = struct.unpack("<I", raw_length)[0]
        if message_length == 0:
            return None
        
        raw_payload = source.read(message_length)
        if len(raw_payload) < message_length:
            return None
            
        return json.loads(raw_payload.decode("utf-8"))

    def write_message(self, stream: Optional[BinaryIO] = None, msg: Optional[dict[str, Any]] = None) -> None:
        target = stream or sys.stdout.buffer
        payload = json.dumps(msg or {}).encode("utf-8")
        target.write(struct.pack("<I", len(payload)))
        target.write(payload)
        target.flush()

    def handle_command(
        self,
        cmd: dict[str, Any],
        queue: Any = None,
        engine: Any = None,
    ) -> dict[str, Any]:
        action = cmd.get("action")
        if not action:
            return {"status": "error", "error": "Missing action in command"}

        if action == "ping":
            return {"status": "ok", "message": "pong"}

        if action == "download":
            url = cmd.get("url")
            output = cmd.get("output", "")
            if not url:
                return {"status": "error", "error": "Missing url"}
            if queue is not None:
                task_id = queue.add_task(url=url, output_path=output)
                return {"status": "ok", "taskId": task_id}
            return {"status": "ok", "message": f"Queued {url}"}

        if action == "query":
            task_id = cmd.get("taskId")
            if queue is not None and task_id:
                status = queue.get_status(task_id)
                return {"status": "ok", "taskStatus": status}
            return {"status": "error", "error": "Task not found"}

        return {"status": "error", "error": f"Unknown action: {action}"}
