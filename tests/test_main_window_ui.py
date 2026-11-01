import os
import tkinter as tk
import pytest
from idm_gui.app import IDMGUIApp


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_main_window_empty_state_card(tk_root):
    app = IDMGUIApp(tk_root)
    assert hasattr(app, "empty_state_frame")
    # Initially empty queue -> empty state card should be placed
    app._tick_ui()
    assert bool(app.empty_state_frame.place_info())

    # Add a task -> empty state should hide (place_forget)
    t = app.queue.add_task("https://example.com/test.zip", "test.zip")
    app._tick_ui()
    assert not bool(app.empty_state_frame.place_info())


def test_main_window_column_headers_in_indonesian(tk_root):
    app = IDMGUIApp(tk_root)
    cols = [app.tree.heading(c, "text") for c in ("name", "size", "status", "progress", "speed", "url")]
    assert "Nama Berkas" in cols
    assert "Ukuran" in cols
    assert "Status" in cols
    assert "Progres" in cols
    assert "Kecepatan" in cols
    assert "URL Unduhan" in cols


def test_main_window_toolbar_responsive_overflow(tk_root):
    app = IDMGUIApp(tk_root)
    assert hasattr(app, "btn_overflow")

    # When width is small (<760), overflow button should be packed
    app._update_toolbar_overflow(width=700)
    assert bool(app.btn_overflow.pack_info())

    # When width is large (>=760), overflow button should be unpacked
    app._update_toolbar_overflow(width=850)
    try:
        is_packed = bool(app.btn_overflow.pack_info())
    except Exception:
        is_packed = False
    assert not is_packed


def test_main_window_tooltips_exist(tk_root):
    app = IDMGUIApp(tk_root)
    assert hasattr(app, "toolbar_buttons")
    assert len(app.toolbar_buttons) >= 6
    # Check that tooltips have been registered
    for btn, tooltip_text in app.toolbar_buttons:
        assert tooltip_text != ""


def test_open_add_url_dialog_structure_and_validation(tk_root, monkeypatch):
    app = IDMGUIApp(tk_root)
    # Ensure clipboard is clear so add_url dialog opens
    monkeypatch.setattr(app.root, "clipboard_get", lambda: "")

    called_urls = []
    monkeypatch.setattr(app, "_show_download_info_for_url", lambda u: called_urls.append(u))

    app.open_add_url_dialog()

    # Find the dialog toplevel child
    toplevels = [w for w in app.root.winfo_children() if isinstance(w, tk.Toplevel)]
    assert len(toplevels) >= 1
    dlg = toplevels[-1]
    assert "URL" in dlg.title()

    # Clean up
    dlg.destroy()


def test_main_window_live_telemetry_cards(tk_root):
    app = IDMGUIApp(tk_root)
    assert hasattr(app, "stat_bar")
    assert hasattr(app, "lbl_stat_speed")
    assert hasattr(app, "lbl_stat_active")
    assert hasattr(app, "lbl_stat_total")

    # Initial state
    app._tick_ui()
    assert "0" in app.lbl_stat_speed.cget("text")
    assert "0" in app.lbl_stat_active.cget("text")

    # Add an active task
    t = app.queue.add_task("https://example.com/live_test.mp4", "live_test.mp4")
    from idm_scheduler.queue import TaskStatus
    app.queue.get_task(t).status = TaskStatus.DOWNLOADING
    app.task_speeds[t] = 1024 * 1024 * 2.5 # 2.5 MB/s
    app._tick_ui()

    assert "2,5" in app.lbl_stat_speed.cget("text") or "2.5" in app.lbl_stat_speed.cget("text")
    assert "1" in app.lbl_stat_active.cget("text")


def test_main_window_modern_sidebar_navigation_and_counts(tk_root):
    app = IDMGUIApp(tk_root)
    assert hasattr(app, "sidebar_items")
    assert "all" in app.sidebar_items
    assert "video" in app.sidebar_items
    assert "finished" in app.sidebar_items

    # Add 1 active video task and 1 finished music task
    t1 = app.queue.add_task("https://example.com/nature.mp4", "nature.mp4")
    from idm_scheduler.queue import TaskStatus
    app.queue.get_task(t1).status = TaskStatus.DOWNLOADING

    t2 = app.queue.add_task("https://example.com/song.mp3", "song.mp3")
    app.queue.get_task(t2).status = TaskStatus.COMPLETED

    app._tick_ui()

    # Check count badges
    assert app.sidebar_items["all"].count == 2
    assert app.sidebar_items["video"].count == 1
    assert app.sidebar_items["music"].count == 1
    assert app.sidebar_items["finished"].count == 1

    # Click video filter
    app._on_sidebar_item_click("video")
    assert app.active_category_filter == "video"

    # Reset to all
    app._on_sidebar_item_click("all")
    assert app.active_category_filter == "all"


def test_main_window_table_modern_layout_and_tags(tk_root):
    app = IDMGUIApp(tk_root)
    t1 = app.queue.add_task("https://example.com/video.mp4", "video.mp4")
    from idm_scheduler.queue import TaskStatus
    app.queue.get_task(t1).status = TaskStatus.DOWNLOADING
    app.queue.get_task(t1).total_bytes = 1000
    app.queue.get_task(t1).bytes_downloaded = 500

    app._tick_ui()

    row_vals = app.tree.item(t1, "values")
    # File name has category glyph
    assert "🎬" in row_vals[0]
    # Status has localized text
    assert "Mengunduh" in row_vals[2]
    # Progress has mini visualizer
    assert "■" in row_vals[3]
    # Tag is downloading
    tags = app.tree.item(t1, "tags")
    assert "downloading" in tags


def test_app_icon_application(tk_root):
    from idm_gui.theme import get_app_icon_path, get_app_png_path, apply_window_icon

    ico = get_app_icon_path()
    assert ico is not None
    assert os.path.exists(ico)

    png = get_app_png_path()
    assert png is not None
    assert os.path.exists(png)

    # Test applying to root without error
    apply_window_icon(tk_root)
    assert hasattr(tk_root, "_app_icon_photo")




