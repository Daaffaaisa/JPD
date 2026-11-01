import os
import sys
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from idm_gui.settings import (
    SettingsManager,
    set_windows_startup,
    get_windows_startup_status,
)


def test_settings_manager_system_options():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = os.path.join(tmpdir, "settings.json")
        sm = SettingsManager(config_path=cfg)

        # Check default values
        assert sm.get_close_to_tray() is True
        assert sm.get_autorun_startup() is True
        assert sm.get_start_minimized() is False
        assert sm.get_play_sound_on_complete() is True
        assert sm.get_confirm_on_delete() is True

        # Mutate values
        sm.set_close_to_tray(False)
        sm.set_autorun_startup(False)
        sm.set_start_minimized(True)
        sm.set_play_sound_on_complete(False)
        sm.set_confirm_on_delete(False)

        # Verify on reloaded instance
        sm2 = SettingsManager(config_path=cfg)
        assert sm2.get_close_to_tray() is False
        assert sm2.get_autorun_startup() is False
        assert sm2.get_start_minimized() is True
        assert sm2.get_play_sound_on_complete() is False
        assert sm2.get_confirm_on_delete() is False


@patch("winreg.OpenKey")
@patch("winreg.SetValueEx")
@patch("winreg.DeleteValue")
def test_windows_startup_helpers(mock_del, mock_set, mock_open):
    # Enable startup
    res = set_windows_startup(True)
    assert res is True
    mock_set.assert_called()

    # Disable startup
    res = set_windows_startup(False)
    assert res is True
    mock_del.assert_called()


def test_options_dialog_has_system_tray_options():
    import tkinter as tk
    from idm_gui.dialogs import OptionsDialog

    root = tk.Tk()
    root.withdraw()
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = os.path.join(tmpdir, "opts.json")
        sm = SettingsManager(config_path=cfg)

        dlg = OptionsDialog(root, settings_mgr=sm)
        assert hasattr(dlg, "cb_close_tray_var")
        assert hasattr(dlg, "cb_sound_var")
        assert hasattr(dlg, "cb_confirm_del_var")
        assert hasattr(dlg, "cb_start_minimized_var")

        # Toggle checkboxes
        dlg.cb_close_tray_var.set(False)
        dlg.cb_sound_var.set(False)
        dlg.cb_confirm_del_var.set(False)
        dlg._on_save()

        assert sm.get_close_to_tray() is False
        assert sm.get_play_sound_on_complete() is False
        assert sm.get_confirm_on_delete() is False

    root.destroy()


def test_app_close_to_tray_and_quit():
    import tkinter as tk
    from idm_gui.app import IDMGUIApp

    root = tk.Tk()
    root.withdraw()

    app = IDMGUIApp(root)
    # Mock settings to close_to_tray = True
    app.settings.set_close_to_tray(True)

    with patch.object(root, "withdraw") as mock_withdraw:
        app._on_close()
        mock_withdraw.assert_called()

    # When quitting explicitly via quit_app
    with patch.object(root, "destroy") as mock_destroy:
        app.quit_app()
        mock_destroy.assert_called()

    root.destroy()
