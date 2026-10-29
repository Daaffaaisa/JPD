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

