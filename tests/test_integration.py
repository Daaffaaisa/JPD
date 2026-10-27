import io
import os
import tempfile
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import pytest

from idm_core.engine import DownloadEngine
from idm_media.parser import StreamParser
from idm_media.muxer import StreamMuxer
from idm_scheduler.queue import DownloadQueue, TaskStatus
from idm_broker.broker import NativeMessageBroker


class SimpleDataHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def file_server():
    with tempfile.TemporaryDirectory() as srv_dir:
        # Create a test file in server dir
        test_file = os.path.join(srv_dir, "sample.bin")
        payload = b"End-to-End Pipeline Verification Data\n" * 50
        with open(test_file, "wb") as f:
            f.write(payload)

        # Start HTTP server serving srv_dir
        class CustomHandler(SimpleDataHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=srv_dir, **kwargs)

        server = HTTPServer(("127.0.0.1", 0), CustomHandler)
        port = server.server_port
        th = threading.Thread(target=server.serve_forever, daemon=True)
        th.start()
        yield f"http://127.0.0.1:{port}/sample.bin", payload
        server.shutdown()


def test_full_e2e_pipeline_broker_queue_engine(file_server):
    url, expected_payload = file_server
    
    engine = DownloadEngine()
    queue = DownloadQueue()
    broker = NativeMessageBroker()

    with tempfile.TemporaryDirectory() as out_dir:
        dest_path = os.path.join(out_dir, "downloaded_sample.bin")
        
        # 1. Browser extension sends a download command via broker
        download_command = {
            "action": "download",
            "url": url,
            "output": dest_path
        }
        broker_resp = broker.handle_command(download_command, queue=queue, engine=engine)
        assert broker_resp["status"] == "ok"
        task_id = broker_resp["taskId"]
        assert task_id is not None

        # 2. Scheduler processes the task
        task = queue.process_next(engine, num_parts=2)
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.bytes_downloaded == len(expected_payload)

        # 3. File content integrity verified
        assert os.path.exists(dest_path)
        with open(dest_path, "rb") as f:
            assert f.read() == expected_payload

        # 4. Browser extension queries status
        query_command = {"action": "query", "taskId": task_id}
        status_resp = broker.handle_command(query_command, queue=queue)
        assert status_resp["status"] == "ok"
        assert status_resp["taskStatus"] == "COMPLETED"


def test_hls_stream_download_and_mux_pipeline():
    # Simulate parsed HLS stream segments being downloaded and muxed
    with tempfile.TemporaryDirectory() as tmpdir:
        seg1 = os.path.join(tmpdir, "chunk0.ts")
        seg2 = os.path.join(tmpdir, "chunk1.ts")
        out_video = os.path.join(tmpdir, "movie.ts")

        with open(seg1, "wb") as f:
            f.write(b"HLS-SEGMENT-0-VIDEO-FRAME")
        with open(seg2, "wb") as f:
            f.write(b"HLS-SEGMENT-1-VIDEO-FRAME")

        muxer = StreamMuxer()
        final_video = muxer.concat_segments([seg1, seg2], out_video)

        assert os.path.exists(final_video)
        with open(final_video, "rb") as f:
            data = f.read()
        assert data == b"HLS-SEGMENT-0-VIDEO-FRAMEHLS-SEGMENT-1-VIDEO-FRAME"
