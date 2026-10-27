from dataclasses import dataclass
from enum import Enum
import threading
from typing import Any, Optional
import uuid


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    DOWNLOADING = "DOWNLOADING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class DownloadTask:
    task_id: str
    url: str
    output_path: str
    status: TaskStatus = TaskStatus.QUEUED
    priority: int = 0
    bytes_downloaded: int = 0
    total_bytes: int = 0
    error: Optional[str] = None


class DownloadQueue:
    """Thread-safe task scheduler and queue manager for downloads."""

    def __init__(self):
        self._tasks: dict[str, DownloadTask] = {}
        self._lock = threading.Lock()

    def add_task(self, url: str, output_path: str, priority: int = 0) -> str:
        with self._lock:
            task_id = str(uuid.uuid4())[:8]
            task = DownloadTask(
                task_id=task_id,
                url=url,
                output_path=output_path,
                priority=priority,
                status=TaskStatus.QUEUED,
            )
            self._tasks[task_id] = task
            return task_id

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_status(self, task_id: str) -> Optional[str]:
        task = self.get_task(task_id)
        return task.status.value if task else None

    def list_tasks(self, status: Optional[TaskStatus] = None) -> list[DownloadTask]:
        with self._lock:
            tasks = list(self._tasks.values())
            if status is not None:
                tasks = [t for t in tasks if t.status == status]
            return sorted(tasks, key=lambda t: t.priority, reverse=True)

    def pause_task(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status in (TaskStatus.QUEUED, TaskStatus.DOWNLOADING):
                task.status = TaskStatus.PAUSED
                return True
            return False

    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    def process_next(self, engine: Any, num_parts: int = 4) -> Optional[DownloadTask]:
        """Picks the highest-priority queued task and executes it with engine."""
        target_task: Optional[DownloadTask] = None
        with self._lock:
            queued = [t for t in self._tasks.values() if t.status == TaskStatus.QUEUED]
            if not queued:
                return None
            queued.sort(key=lambda t: t.priority, reverse=True)
            target_task = queued[0]
            target_task.status = TaskStatus.DOWNLOADING

        def on_progress(chunk_len: int):
            with self._lock:
                target_task.bytes_downloaded += chunk_len

        res = engine.download(
            target_task.url,
            target_task.output_path,
            num_parts=num_parts,
            progress_callback=on_progress,
        )

        with self._lock:
            if res.success:
                target_task.status = TaskStatus.COMPLETED
                target_task.bytes_downloaded = res.bytes_downloaded
                target_task.total_bytes = res.bytes_downloaded
                target_task.error = None
            else:
                target_task.status = TaskStatus.FAILED
                target_task.error = res.error or "Unknown download error"
        return target_task
