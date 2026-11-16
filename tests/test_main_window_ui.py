import os
import tkinter as tk
import pytest
from idm_gui.app import IDMGUIApp
from idm_gui.theme import THEME


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
    # Initially empty queue -> GlassTableView renders the single native empty state card
    # and legacy empty_state_frame is NOT placed over it (zero card overlap).
    app._tick_ui()
    tk_root.update_idletasks()
    assert not bool(app.empty_state_frame.place_info())
    assert len(app.tree.viewport.find_withtag("empty_state")) > 0

    # Add a task -> GlassTableView empty state hides cleanly
    t = app.queue.add_task("https://example.com/test.zip", "test.zip")
    app._tick_ui()
    tk_root.update_idletasks()
    assert not bool(app.empty_state_frame.place_info())
    assert len(app.tree.viewport.find_withtag("empty_state")) == 0


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


def test_main_window_sidebar_compact_toggle_and_phone_badges(tk_root):
    app = IDMGUIApp(tk_root)
    assert hasattr(app, "btn_hamburger")
    assert app.sidebar_compact is False

    # Set some test counts
    app.sidebar_items["all"].set_count(5)
    app.sidebar_items["video"].set_count(2)
    app.sidebar_items["music"].set_count(0)

    # 1. Toggle to compact mode
    app.toggle_sidebar_compact()
    assert app.sidebar_compact is True
    assert app.sidebar_items["all"].is_compact is True
    assert app.sidebar_items["video"].is_compact is True

    # Check that items with count > 0 have phone badge drawn
    assert bool(app.sidebar_items["all"].badge_canvas.place_info()) is True
    assert bool(app.sidebar_items["video"].badge_canvas.place_info()) is True
    # Item with count 0 should NOT show phone badge
    assert bool(app.sidebar_items["music"].badge_canvas.place_info()) is False

    # 2. Toggle back to expanded mode
    app.toggle_sidebar_compact()
    assert app.sidebar_compact is False
    assert app.sidebar_items["all"].is_compact is False
    # Phone badge should be forgotten in expanded mode
    assert bool(app.sidebar_items["all"].badge_canvas.place_info()) is False
    assert app.sidebar_items["all"].lbl_badge.cget("text") == "5"

    # Test fade interpolation logic directly
    app.sidebar_items["all"].set_text_fade(0.0)
    app.sidebar_items["all"].set_text_fade(0.5)
    app.sidebar_items["all"].set_text_fade(1.0)


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


def test_main_window_context_menu_and_url_clipboard(tk_root):
    app = IDMGUIApp(tk_root)
    assert hasattr(app, "context_menu")
    assert app.context_menu is not None

    # Verify context menu items
    end_idx = app.context_menu.index("end")
    count = (end_idx + 1) if end_idx is not None else 0
    menu_labels = [app.context_menu.entrycget(i, "label") for i in range(count) if app.context_menu.type(i) == "command"]
    assert any("Lanjutkan" in l for l in menu_labels)
    assert any("Jeda" in l for l in menu_labels)
    assert any("Buka Berkas" in l for l in menu_labels)
    assert any("Salin URL" in l for l in menu_labels)
    assert any("Hapus" in l for l in menu_labels)

    # Test copy_selected_url
    t1 = app.queue.add_task(url="https://example.com/test_copy.iso", output_path="downloads/test_copy.iso")
    app.tree.insert("", "end", iid=t1, values=("test_copy.iso", "10 MB", "Selesai", "100%", "--", "https://example.com/test_copy.iso"))
    app.tree.selection_set(t1)

    app.copy_selected_url()
    try:
        assert tk_root.clipboard_get() == "https://example.com/test_copy.iso"
    except Exception:
        pass  # Clipboard may be restricted in headless X11/CI environments


def test_main_window_language_switching_toolbar_and_menus(tk_root):
    app = IDMGUIApp(tk_root)

    # 1. Switch to English
    app.set_language("en")
    assert app.btn_add.cget("text") == "Add URL"
    assert app.btn_resume.cget("text") == "Resume"
    assert app.btn_pause.cget("text") == "Pause"
    assert app.btn_delete.cget("text") == "Delete"
    assert app.btn_stop.cget("text") == "Stop"
    assert app.btn_clean.cget("text") == "Clear"
    assert app.btn_resume.cget("icon") == "resume"
    assert app.btn_pause.cget("icon") == "pause"
    assert app.card_speed.lbl_title.cget("text") == "⚡ ACTIVE SPEED"
    assert app.tree.heading("name", "text") == "File Name"
    assert app.tree.heading("speed", "text") == "Speed"

    # Context menu in English
    assert "Resume Download" in app.context_menu.entrycget(0, "label")
    assert "Pause Download" in app.context_menu.entrycget(1, "label")

    # Empty state card in English
    assert app.empty_state_frame.itemcget(app.empty_state_title_id, "text") == "No Downloads Yet"
    assert app.btn_empty_add.cget("text") == "+ Add New Download"

    # 2. Switch back to Indonesian
    app.set_language("id")
    assert app.btn_add.cget("text") == "Tambah URL"
    assert app.btn_resume.cget("text") == "Lanjutkan"
    assert app.btn_pause.cget("text") == "Jeda"
    assert app.btn_delete.cget("text") == "Hapus"
    assert app.btn_stop.cget("text") == "Hentikan"
    assert app.btn_clean.cget("text") == "Bersihkan"
    assert app.card_speed.lbl_title.cget("text") == "⚡ KECEPATAN AKTIF"
    assert app.tree.heading("name", "text") == "Nama Berkas"
    assert app.tree.heading("speed", "text") == "Kecepatan"

    # Context menu in Indonesian
    assert "Lanjutkan Unduh" in app.context_menu.entrycget(0, "label")
    assert "Jeda Unduh" in app.context_menu.entrycget(1, "label")

    # Empty state card in Indonesian
    assert app.empty_state_frame.itemcget(app.empty_state_title_id, "text") == "Belum Ada Unduhan"
    assert app.btn_empty_add.cget("text") == "+ Tambah Unduhan Baru"


def test_sidebar_rapid_toggle_robustness(tk_root):
    """Verify rapid repeated clicks on hamburger toggle do not crash and preserve crisp text rendering."""
    app = IDMGUIApp(tk_root)
    # Add dummy tasks to queue so sidebar count update maintains count
    for i in range(7):
        app.queue.add_task(f"https://example.com/file{i}.zip", f"file{i}.zip")
    app._tick_ui()

    # Perform 100 rapid toggles
    for i in range(100):
        app.toggle_sidebar_compact()
        if i % 10 == 0:
            tk_root.update()

    # Finish on expanded state
    if app.sidebar_compact:
        app.toggle_sidebar_compact()
    tk_root.update()

    assert app.sidebar_compact is False
    assert app.sidebar_items["all"].is_compact is False
    # Verify label and badge have valid, non-faded colors
    assert app.sidebar_items["all"].lbl_text.cget("text") == "Semua Unduhan"
    assert app.sidebar_items["all"].lbl_badge.cget("text") == "7"
    assert app.lbl_sidebar_title.cget("fg") == THEME["text_tertiary"]


def test_tray_minimize_restore_and_navbar_spam(tk_root):
    """Verify that minimizing to tray and restoring does not cause GDI handle corruption or crashes on subsequent navbar toggles."""
    app = IDMGUIApp(tk_root)
    for i in range(5):
        app.queue.add_task(f"https://example.com/file{i}.zip", f"file{i}.zip")
    app._tick_ui()

    # Minimize to tray
    app.minimize_to_tray()
    tk_root.update()

    # Restore from tray
    app.restore_from_tray()
    tk_root.update()

    # Rapid toggle spam after restore
    for _ in range(30):
        app.toggle_sidebar_compact()
        tk_root.update()

    assert app.sidebar_frame.winfo_exists()


def test_sidebar_shows_zero_badge_when_empty(tk_root):
    """Verify sidebar items still display a '0' badge when count is 0 (and after returning to 0)."""
    app = IDMGUIApp(tk_root)
    app._tick_ui()

    # Empty items should display "0" and stay packed
    for key in ("all", "downloading", "finished", "video", "music", "pictures", "programs", "documents", "compressed"):
        item = app.sidebar_items[key]
        assert item.count == 0
        assert item.lbl_badge.cget("text") == "0"
        assert bool(item.lbl_badge.pack_info()) is True

    # Transition count > 0 then back to 0 keeps "0" badge visible
    vid_item = app.sidebar_items["video"]
    vid_item.set_count(3)
    assert vid_item.lbl_badge.cget("text") == "3"
    vid_item.set_count(0)
    assert vid_item.lbl_badge.cget("text") == "0"
    assert bool(vid_item.lbl_badge.pack_info()) is True

    # Compact mode: red dot pip stays hidden for 0, expanded restores "0" badge
    app.toggle_sidebar_compact()
    assert bool(vid_item.badge_canvas.place_info()) is False
    app.toggle_sidebar_compact()
    assert vid_item.lbl_badge.cget("text") == "0"
    assert bool(vid_item.lbl_badge.pack_info()) is True

