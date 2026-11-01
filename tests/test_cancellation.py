import os
import tempfile
import threading
import time
import pytest

from idm_core.engine import DownloadEngine, DownloadResult
from idm_scheduler.queue import DownloadQueue, TaskStatus


def test_engine_stops_when_stop_event_set():
    engine = DownloadEngine()
    stop_event = threading.Event()

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test.bin")
        # We simulate a stop event already set or set after 1 chunk
        stop_event.set()

        # Engine download should accept stop_event and abort immediately
        res = engine.download(
            "https://raw.githubusercontent.com/python/cpython/main/LICENSE",
            out_file,
            num_parts=2,
            stop_event=stop_event,
        )

        assert res.success is False
        assert "stop" in res.error.lower() or "pause" in res.error.lower() or "cancel" in res.error.lower()


def test_app_pause_and_cancel_signals_stop_event():
    from idm_gui.app import IDMGUIApp
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    app = IDMGUIApp(root)

    task_id = app.queue.add_task(url="https://example.com/test.zip", output_path="test.zip")
    task = app.queue.get_task(task_id)
    task.status = TaskStatus.DOWNLOADING

    # Register a stop event for this task
    ev = threading.Event()
    app.stop_events[task_id] = ev

    # Pause task
    app.pause_task_by_id(task_id)
    assert ev.is_set() is True
    assert task.status == TaskStatus.PAUSED

    # Reset event and test delete / cancel
    ev.clear()
    task.status = TaskStatus.DOWNLOADING
    app.delete_task_by_id(task_id)
    assert ev.is_set() is True
    assert app.queue.get_task(task_id) is None

    app.quit_app()


def test_cancel_from_pre_download_dialog_removes_task_completely():
    from idm_gui.app import IDMGUIApp
    from idm_gui.dialogs import DialogAction, DownloadInfoDialog
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    app = IDMGUIApp(root)

    # 1. Server receives /api/download and adds task to queue
    task_id = app.queue.add_task(url="https://example.com/movie.mp4", output_path="movie.mp4")
    assert app.queue.get_task(task_id) is not None

    # 2. Simulate dialog being opened and user clicking Batal / Cancel
    # In app.py: on_dialog_action is defined inside handle_incoming
    # Let's test calling delete_task_by_id via on_dialog_action
    dlg = DownloadInfoDialog(
        parent=root,
        url="https://example.com/movie.mp4",
        title="movie.mp4",
        on_action=lambda action, url, path, parts: app.delete_task_by_id(task_id) if action == DialogAction.CANCEL else None
    )

    # User clicks Batal
    dlg._on_cancel()

    # 3. Verify task is completely removed from queue and tree
    assert app.queue.get_task(task_id) is None
    assert app.tree.exists(task_id) is False

    app.quit_app()

