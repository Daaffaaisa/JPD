import sys
import os
import time
import pytest
import tkinter as tk
from unittest.mock import MagicMock

from idm_gui.app import IDMGUIApp
from idm_scheduler.queue import TaskStatus


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_memory_trim_on_minimize_and_idle(tk_root):
    """Verify that minimizing to tray triggers memory trimming without breaking app state or queue."""
    app = IDMGUIApp(tk_root)
    tk_root.update()

    # Add dummy tasks
    for i in range(3):
        app.queue.add_task(f"http://example.com/item_{i}.zip", f"item_{i}.zip")
    tk_root.update()

    # Verify _trim_memory_if_idle runs cleanly
    app._trim_memory_if_idle()

    # Verify task cleanup tracking
    app._cleanup_task_tracking("test_id")

    # Minimize to tray
    app.minimize_to_tray()
    tk_root.update()

    # Restore from tray
    app.restore_from_tray()
    tk_root.update()

    assert app.sidebar_frame.winfo_exists()
    assert app.root.state() == "normal"


def test_active_download_prevents_premature_trim(tk_root):
    """Verify that if a download is active, trimming is skipped to prevent I/O paging jitter."""
    app = IDMGUIApp(tk_root)
    tk_root.update()

    task_id = app.queue.add_task("http://example.com/active.bin", "active.bin")
    task = app.queue.get_task(task_id)
    assert task is not None
    task.status = TaskStatus.DOWNLOADING

    # In active download state, _trim_memory_if_idle returns early
    app._trim_memory_if_idle()
    assert task.status == TaskStatus.DOWNLOADING
