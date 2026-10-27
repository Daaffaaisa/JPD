import os
import tempfile
import tkinter as tk
import pytest

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


def test_gui_menus_exist(tk_root):
    app = IDMGUIApp(tk_root)
    assert app.root.cget("menu") != ""
    # Verify menu bar has items
    menubar = app.menubar
    assert menubar is not None
    # Menus: Tugas, Berkas, Unduh, Lihat, Bantuan
    menu_labels = [menubar.entrycget(i, "label") for i in range(menubar.index("end") + 1)]
    assert any("Tugas" in m or "Tasks" in m for m in menu_labels)
    assert any("Berkas" in m or "File" in m for m in menu_labels)
    assert any("Unduh" in m or "Downloads" in m for m in menu_labels)
    assert any("Lihat" in m or "View" in m for m in menu_labels)
    assert any("Bantuan" in m or "Help" in m for m in menu_labels)


def test_gui_pause_all_and_resume_all(tk_root):
    app = IDMGUIApp(tk_root)
    # Add two tasks
    t1 = app.queue.add_task("https://example.com/file1.bin", "f1.bin")
    t2 = app.queue.add_task("https://example.com/file2.bin", "f2.bin")
    app.queue.get_task(t1).status = TaskStatus.DOWNLOADING
    app.queue.get_task(t2).status = TaskStatus.DOWNLOADING

    # Pause All
    app.pause_all()
    assert app.queue.get_task(t1).status == TaskStatus.PAUSED
    assert app.queue.get_task(t2).status == TaskStatus.PAUSED

    # Resume All
    app.resume_all()
    assert app.queue.get_task(t1).status in (TaskStatus.DOWNLOADING, TaskStatus.QUEUED)
    assert app.queue.get_task(t2).status in (TaskStatus.DOWNLOADING, TaskStatus.QUEUED)


def test_gui_delete_completed(tk_root):
    app = IDMGUIApp(tk_root)
    t1 = app.queue.add_task("https://example.com/completed.bin", "c.bin")
    t2 = app.queue.add_task("https://example.com/active.bin", "a.bin")
    app.queue.get_task(t1).status = TaskStatus.COMPLETED
    app.queue.get_task(t2).status = TaskStatus.DOWNLOADING

    app.delete_completed()
    assert app.queue.get_task(t1) is None
    assert app.queue.get_task(t2) is not None


def test_gui_import_and_export_text_file(tk_root):
    app = IDMGUIApp(tk_root)
    with tempfile.TemporaryDirectory() as tmpdir:
        export_file = os.path.join(tmpdir, "exported_urls.txt")
        app.queue.add_task("https://example.com/item1.zip", "item1.zip")
        app.queue.add_task("https://example.com/item2.zip", "item2.zip")

        app.export_to_text_file(export_file)
        assert os.path.exists(export_file)
        with open(export_file, "r") as f:
            content = f.read()
            assert "https://example.com/item1.zip" in content
            assert "https://example.com/item2.zip" in content

        # Create another app and import
        app2 = IDMGUIApp(tk_root)
        app2.import_from_text_file(export_file)
        imported_urls = [t.url for t in app2.queue.list_tasks()]
        assert "https://example.com/item1.zip" in imported_urls
        assert "https://example.com/item2.zip" in imported_urls
