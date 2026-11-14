import os
import tkinter as tk
from unittest.mock import MagicMock
import pytest

from idm_gui.i18n import (
    tr,
    get_current_lang,
    format_size_id,
    format_time_left,
    get_category_display_name,
    get_canonical_category_key,
    CATEGORY_KEYS,
)
from idm_gui.settings import SettingsManager
from idm_gui.app import IDMGUIApp
from idm_gui.dialogs import (
    DownloadInfoDialog,
    DownloadProgressDialog,
    OptionsDialog,
    DownloadCompleteDialog,
)


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_i18n_formatters_and_category_helpers():
    # 1. format_size_id in ID and EN
    assert format_size_id(0, lang="id") == "Tidak diketahui"
    assert format_size_id(0, lang="en") == "Unknown"
    assert format_size_id(int(337.84 * 1024 * 1024), lang="id") == "337,84 MB"
    assert format_size_id(int(337.84 * 1024 * 1024), lang="en") == "337.84 MB"

    # 2. format_time_left in ID and EN
    assert format_time_left(0, lang="id") in ("Selesai", "✓ Selesai")
    assert format_time_left(0, lang="en") in ("Complete", "Finished", "✓ Completed")
    assert format_time_left(45, lang="id") == "45 detik"
    assert format_time_left(45, lang="en") == "45 sec"
    assert format_time_left(13 * 60 + 58, lang="id") == "13 menit 58 detik"
    assert format_time_left(13 * 60 + 58, lang="en") == "13 min 58 sec"
    assert format_time_left(3600 + 120, lang="id") == "1 jam 2 menit"
    assert format_time_left(3600 + 120, lang="en") == "1 hr 2 min"

    # 3. Category display names
    assert get_category_display_name("Musik", lang="id") == "Musik"
    assert get_category_display_name("Musik", lang="en") == "Music"
    assert get_category_display_name("Berkas Terkompresi", lang="id") in ("Terkompresi", "Berkas Terkompresi")
    assert get_category_display_name("Berkas Terkompresi", lang="en") == "Compressed"
    assert get_category_display_name("Gambar", lang="en") == "Pictures"

    # 4. Canonical category key mapping
    assert get_canonical_category_key("Music") == "Musik"
    assert get_canonical_category_key("Musik") == "Musik"
    assert get_canonical_category_key("Compressed") == "Berkas Terkompresi"
    assert get_canonical_category_key("Terkompresi") == "Berkas Terkompresi"
    assert get_canonical_category_key("Pictures") == "Gambar"
    assert get_canonical_category_key("Programs") == "Program"
    assert get_canonical_category_key("General") == "Umum"


def test_main_window_full_language_switching(tk_root):
    app = IDMGUIApp(tk_root)

    # Switch to English
    app.set_language("en")

    # 1. Toolbar texts & tooltips
    assert app.btn_add.cget("text") == "Add URL"
    assert app.btn_add.tooltip_obj.text == "Add New URL (Ctrl+N)"
    assert app.btn_resume.cget("text") == "Resume"
    assert app.btn_resume.tooltip_obj.text == "Resume Selected Download"
    assert app.btn_pause.cget("text") == "Pause"
    assert app.btn_pause.tooltip_obj.text == "Pause Selected Download"
    assert app.btn_delete.cget("text") == "Delete"
    assert app.btn_delete.tooltip_obj.text == "Delete Selected Download (Del)"
    assert app.btn_stop.cget("text") == "Stop"
    assert app.btn_stop.tooltip_obj.text == "Stop All Downloads"
    assert app.btn_clean.cget("text") == "Clear"
    assert app.btn_clean.tooltip_obj.text == "Clear All Completed Downloads"
    assert app.btn_folder.cget("text") == "Open Folder"
    assert app.btn_folder.tooltip_obj.text == "Open Selected File Folder"
    assert app.btn_opts.cget("text") == "Settings"
    assert app.btn_opts.tooltip_obj.text == "Just Press Download Configuration Options"

    # 2. Sidebar headers and items
    assert app.lbl_sidebar_title.cget("text") == "NAVIGATION"
    assert app.lbl_sec_pustaka.cget("text") == "LIBRARY"
    assert app.lbl_sec_kategori.cget("text") == "FILE CATEGORIES"
    assert app.sidebar_items["all"].raw_text == "All Downloads"
    assert app.sidebar_items["downloading"].raw_text == "Downloading"
    assert app.sidebar_items["finished"].raw_text == "Finished"
    assert app.sidebar_items["music"].raw_text == "Music"
    assert app.sidebar_items["pictures"].raw_text == "Pictures"
    assert app.sidebar_items["compressed"].raw_text == "Compressed"

    # 3. Storage card
    assert app.storage_card.lbl_title.cget("text") == "STORAGE"
    assert app.storage_card.btn_open.cget("text") == "Open Folder"
    assert app.storage_card.btn_open.tooltip_obj.text == "Open Selected File Folder"

    # 4. Table headings
    assert app.tree.heading("name", "text") == "File Name"
    assert app.tree.heading("size", "text") == "Size"
    assert app.tree.heading("status", "text") == "Status"
    assert app.tree.heading("progress", "text") == "Progress"
    assert app.tree.heading("speed", "text") == "Speed"
    assert app.tree.heading("url", "text") == "Download URL"

    # 5. Context menu & overflow menu
    assert "Resume Download" in app.context_menu.entrycget(0, "label")
    assert "Open File" in app.context_menu.entrycget(3, "label")
    assert "Clear" in app.overflow_menu.entrycget(1, "label")

    # 6. Tray menu if available
    if hasattr(app, "tray_menu_items") and app.tray_menu_items:
        labels = [item.text for item in app.tray_menu_items if hasattr(item, "text")]
        assert any("Open Just Press Download" in l for l in labels)
        assert any("Resume All Downloads" in l for l in labels)

    # 7. Tray notification strings
    assert tr("tray_notify_minimized", lang="en") == "Application minimized to System Tray"
    assert tr("tray_notify_minimized", lang="id") == "Aplikasi diminimalkan ke System Tray"

    mock_tray = MagicMock()
    app.tray_icon = mock_tray
    app.set_language("en")
    app.minimize_to_tray()
    mock_tray.notify.assert_called_with("Application minimized to System Tray", "Just Press Download")

    app.set_language("id")
    app.minimize_to_tray()
    mock_tray.notify.assert_called_with("Aplikasi diminimalkan ke System Tray", "Just Press Download")

    # Switch back to Indonesian
    app.set_language("id")
    assert app.btn_add.cget("text") == "Tambah URL"
    assert app.btn_add.tooltip_obj.text == "Tambah URL Baru (Ctrl+N)"
    assert app.lbl_sidebar_title.cget("text") == "NAVIGASI"
    assert app.sidebar_items["music"].raw_text == "Musik"
    assert app.sidebar_items["compressed"].raw_text in ("Terkompresi", "Berkas Terkompresi")
    assert app.storage_card.lbl_title.cget("text") == "PENYIMPANAN"
    assert app.storage_card.btn_open.cget("text") == "Buka Folder"


def test_download_info_dialog_language(tk_root):
    from idm_gui.settings import settings

    # Test in English
    settings.set_language("en")
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/test.zip",
        title="test.zip",
        probed_size=1024 * 1024 * 10,
        category="Berkas Terkompresi",
    )
    assert dlg.top.title() == "Download File Info"
    assert "Music" in dlg.cat_cb["values"]
    assert "Compressed" in dlg.cat_cb["values"]
    assert dlg.cat_var.get() == "Compressed"
    assert dlg.btn_add_cat.tooltip_obj.text == "Add New Category..."
    assert dlg.btn_browse.tooltip_obj.text == "Select Save Folder..."
    assert "Remember this path for category 'Compressed'" in dlg.cb_remember.cget("text")
    dlg.top.destroy()

    # Test in Indonesian
    settings.set_language("id")
    dlg2 = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/test.zip",
        title="test.zip",
        probed_size=1024 * 1024 * 10,
        category="Berkas Terkompresi",
    )
    assert dlg2.top.title() == "Info Unduh Berkas"
    assert "Musik" in dlg2.cat_cb["values"]
    assert "Terkompresi" in dlg2.cat_cb["values"] or "Berkas Terkompresi" in dlg2.cat_cb["values"]
    assert dlg2.btn_add_cat.tooltip_obj.text == "Tambah Kategori Baru..."
    assert dlg2.btn_browse.tooltip_obj.text == "Pilih Folder Penyimpanan..."
    dlg2.top.destroy()


def test_download_progress_dialog_language(tk_root):
    from idm_gui.settings import settings

    # Test in English
    settings.set_language("en")
    dlg = DownloadProgressDialog(
        parent=tk_root,
        task_id="t_i18n",
        url="https://example.com/movie.mp4",
        output_path="C:/Downloads/movie.mp4",
        total_bytes=1000000,
        parts=4,
    )
    assert dlg.lbl_tab1.cget("text") == "Download status"
    assert dlg.lbl_tab2.cget("text") == "Speed Limiter"
    assert dlg.lbl_tab3.cget("text") == "Completion Options"
    assert dlg.btn_cancel.cget("text") == "Cancel"
    assert dlg.btn_pause.cget("text") == "Pause"
    assert dlg.btn_toggle.cget("text") == "<< Hide details"
    assert dlg.conn_tree.heading("num", "text") == "Connection"
    assert dlg.conn_tree.heading("dl", "text") == "Downloaded"
    assert dlg.conn_tree.heading("info", "text") == "Status"
    dlg.close()

    # Test in Indonesian
    settings.set_language("id")
    dlg2 = DownloadProgressDialog(
        parent=tk_root,
        task_id="t_i18n_id",
        url="https://example.com/movie.mp4",
        output_path="C:/Downloads/movie.mp4",
        total_bytes=1000000,
        parts=4,
    )
    assert dlg2.lbl_tab1.cget("text") == "Status unduhan"
    assert dlg2.lbl_tab2.cget("text") == "Pembatas Kecepatan"
    assert dlg2.lbl_tab3.cget("text") == "Opsi saat selesai"
    assert dlg2.btn_cancel.cget("text") == "Batal"
    assert dlg2.btn_pause.cget("text") == "Jeda"
    assert dlg2.btn_toggle.cget("text") == "<< Sembunyikan detail"
    assert dlg2.conn_tree.heading("num", "text") == "Koneksi"
    dlg2.close()


def test_options_dialog_full_language_and_live_sync(tk_root):
    from idm_gui.settings import settings

    # Set to English and check OptionsDialog
    settings.set_language("en")
    dlg = OptionsDialog(parent=tk_root, settings_manager=settings)
    assert dlg.top.title() == "Just Press Download Configuration Options"
    assert dlg.btn_save.cget("text") == "Save"
    assert dlg.btn_cancel.cget("text") == "Cancel"
    assert dlg.notebook.tab(0, "text") == "General"
    assert dlg.notebook.tab(1, "text") == "File Types"
    assert dlg.notebook.tab(2, "text") == "Save To"
    assert dlg.notebook.tab(3, "text") == "Connection"
    assert "Music" in dlg.cat_combo["values"]
    assert "Compressed" in dlg.cat_combo["values"]
    dlg.top.destroy()

    # Set to Indonesian and check OptionsDialog
    settings.set_language("id")
    dlg2 = OptionsDialog(parent=tk_root, settings_manager=settings)
    assert dlg2.top.title() == "Opsi Konfigurasi Just Press Download"
    assert dlg2.btn_save.cget("text") == "Simpan"
    assert dlg2.btn_cancel.cget("text") == "Batal"
    assert dlg2.notebook.tab(0, "text") == "Umum"
    assert dlg2.notebook.tab(1, "text") == "Jenis Berkas"
    assert dlg2.notebook.tab(2, "text") == "Simpan ke"
    assert dlg2.notebook.tab(3, "text") == "Koneksi"
    dlg2.top.destroy()
