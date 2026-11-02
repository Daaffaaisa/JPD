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


def test_queue_save_and_load_file():
    queue = DownloadQueue()
    t1 = queue.add_task("https://example.com/file1.zip", "downloads/file1.zip")
    t2 = queue.add_task("https://example.com/file2.mp4", "downloads/file2.mp4")

    task1 = queue.get_task(t1)
    assert task1 is not None
    task1.status = TaskStatus.COMPLETED
    task1.bytes_downloaded = 1000
    task1.total_bytes = 1000

    task2 = queue.get_task(t2)
    assert task2 is not None
    task2.status = TaskStatus.DOWNLOADING
    task2.bytes_downloaded = 250
    task2.total_bytes = 500

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "tasks.json")
        saved = queue.save_to_file(json_path)
        assert saved is True
        assert os.path.exists(json_path)

        queue2 = DownloadQueue()
        loaded = queue2.load_from_file(json_path)
        assert loaded is True

        loaded_t1 = queue2.get_task(t1)
        assert loaded_t1 is not None
        assert loaded_t1.status == TaskStatus.COMPLETED
        assert loaded_t1.bytes_downloaded == 1000

        loaded_t2 = queue2.get_task(t2)
        assert loaded_t2 is not None
        # Tasks that were DOWNLOADING when closed should safely restore as PAUSED
        assert loaded_t2.status == TaskStatus.PAUSED
        assert loaded_t2.bytes_downloaded == 250
