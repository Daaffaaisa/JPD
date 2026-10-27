import os
import tempfile
import tkinter as tk
import pytest

from idm_gui.settings import SettingsManager


def test_options_dialog_saves_category_path(monkeypatch):
    from idm_gui.dialogs import OptionsDialog

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = os.path.join(tmpdir, "test_settings.json")
        sm = SettingsManager(config_path=cfg)

        root = tk.Tk()
        root.withdraw()

        dlg = OptionsDialog(parent=root, settings_manager=sm)

        # Select category 'Video' and set a new path
        new_video_dir = os.path.join(tmpdir, "MyCustomVideoFolder")
        dlg.cat_var.set("Video")
        dlg._on_cat_change()
        dlg.path_var.set(new_video_dir)

        # Click OK / Simpan
        dlg._on_save()

        # Check that it's persisted in the settings manager
        assert sm.get_category_path("Video") == os.path.abspath(new_video_dir)

        root.destroy()


def test_options_dialog_saves_max_connections():
    from idm_gui.dialogs import OptionsDialog

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = os.path.join(tmpdir, "test_settings.json")
        sm = SettingsManager(config_path=cfg)

        root = tk.Tk()
        root.withdraw()

        dlg = OptionsDialog(parent=root, settings_manager=sm)
        assert dlg.conn_var.get() in ("8", "16", "32")

        # Change connection limit to 32
        dlg.conn_var.set("32")
        dlg._on_save()

        assert sm.get_max_connections() == 32
        root.destroy()


def test_options_dialog_has_idm_tabs():
    from idm_gui.dialogs import OptionsDialog

    root = tk.Tk()
    root.withdraw()

    dlg = OptionsDialog(parent=root)
    assert hasattr(dlg, "notebook")
    tab_names = [dlg.notebook.tab(i, "text") for i in dlg.notebook.tabs()]
    assert any("Umum" in t or "General" in t for t in tab_names)
    assert any("Jenis Berkas" in t or "File Types" in t for t in tab_names)
    assert any("Simpan" in t or "Save" in t for t in tab_names)
    assert any("Koneksi" in t or "Connection" in t for t in tab_names)
    dlg.top.destroy()
    root.destroy()


def test_options_dialog_saves_and_loads_browser_and_autorun_settings():
    from idm_gui.dialogs import OptionsDialog

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = os.path.join(tmpdir, "test_settings.json")
        sm = SettingsManager(config_path=cfg)

        root = tk.Tk()
        root.withdraw()

        dlg = OptionsDialog(parent=root, settings_manager=sm)
        # Modify settings in Tab 1
        dlg.cb_chrome_var.set(False)
        dlg.cb_opera_var.set(True)
        dlg.cb_startup_var.set(False)
        dlg.cb_clipboard_var.set(False)

        dlg._on_save()

        # Check saved data in SettingsManager
        assert sm.data["browser_integration"]["chrome"] is False
        assert sm.data["browser_integration"]["opera"] is True
        assert sm.data["autorun_startup"] is False
        assert sm.data["monitor_clipboard"] is False

        # Open second dialog and verify values are restored
        dlg2 = OptionsDialog(parent=root, settings_manager=sm)
        assert dlg2.cb_chrome_var.get() is False
        assert dlg2.cb_opera_var.get() is True
        assert dlg2.cb_startup_var.get() is False
        assert dlg2.cb_clipboard_var.get() is False

        dlg2.top.destroy()
        root.destroy()


