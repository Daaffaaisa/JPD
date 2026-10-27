import os
import tempfile
import pytest

from idm_scheduler.queue import DownloadQueue, TaskStatus, DownloadTask
from idm_core.engine import DownloadResult


class DummyEngine:
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed

    def download(self, url, output_path, num_parts=4, progress_callback=None):
        if self.should_succeed:
            with open(output_path, "wb") as f:
                f.write(b"mock content")
            return DownloadResult(
                success=True,
                bytes_downloaded=12,
                num_parts=1,
                output_path=output_path,
            )
        else:
            return DownloadResult(
                success=False,
                bytes_downloaded=0,
                num_parts=1,
                output_path=output_path,
                error="Network failure",
            )


def test_queue_add_and_query_tasks():
    queue = DownloadQueue()
    task_id = queue.add_task(url="https://example.com/test.iso", output_path="downloads/test.iso")
    
    assert task_id is not None
    assert queue.get_status(task_id) == TaskStatus.QUEUED.value
    task = queue.get_task(task_id)
    assert task is not None
    assert task.url == "https://example.com/test.iso"


def test_queue_processes_task_with_engine():
    queue = DownloadQueue()
    dummy_engine = DummyEngine(should_succeed=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "test.bin")
        task_id = queue.add_task(url="https://example.com/test.bin", output_path=dest)

        # Process next task
        processed = queue.process_next(dummy_engine)
        assert processed is not None
        assert processed.task_id == task_id
        assert processed.status == TaskStatus.COMPLETED
        assert processed.bytes_downloaded == 12
        assert os.path.exists(dest)


def test_queue_handles_engine_failure():
    queue = DownloadQueue()
    failing_engine = DummyEngine(should_succeed=False)

    dest = "dummy_path.bin"
    task_id = queue.add_task(url="https://example.com/fail.bin", output_path=dest)

    processed = queue.process_next(failing_engine)
    assert processed is not None
    assert processed.status == TaskStatus.FAILED
    assert processed.error == "Network failure"
