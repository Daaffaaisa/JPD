import pytest
import tkinter as tk
from unittest.mock import MagicMock
from idm_gui.dialogs import DownloadProgressDialog


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_progress_dialog_tab_switching(tk_root):
    speed_changes = []

    dlg = DownloadProgressDialog(
        parent=tk_root,
        task_id="t_tab_switch",
        url="https://example.com/movie.mp4",
        output_path="C:/Downloads/movie.mp4",
        total_bytes=1000000,
        parts=4,
        on_speed_limit_change=lambda limit: speed_changes.append(limit),
    )

    assert hasattr(dlg, "tab1_frame")
    assert hasattr(dlg, "tab2_frame")
    assert hasattr(dlg, "tab3_frame")

    # Initial active tab should be tab 1
    assert dlg.active_tab == 1

    # Switch to tab 2 (Pembatas Kecepatan)
    dlg._switch_tab(2)
    assert dlg.active_tab == 2
    assert hasattr(dlg, "speed_limit_enabled_var")
    assert hasattr(dlg, "speed_limit_val_var")

    # Enable speed limiter and change speed
    dlg.speed_limit_enabled_var.set(True)
    dlg.speed_limit_val_var.set("512")
    dlg._apply_speed_limit()
    assert len(speed_changes) > 0
    assert speed_changes[-1] == 512 * 1024  # 512 KB/s in bps

    # Switch to tab 3 (Opsi saat selesai)
    dlg._switch_tab(3)
    assert dlg.active_tab == 3
    assert hasattr(dlg, "cb_auto_close_var")
    assert hasattr(dlg, "cb_shutdown_var")
    assert hasattr(dlg, "cb_disconnect_var")

    # Switch back to tab 1
    dlg._switch_tab(1)
    assert dlg.active_tab == 1

    dlg.close()
