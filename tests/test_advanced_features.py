import os
import tempfile
import tkinter as tk
import pytest

from idm_gui.dialogs import DownloadCompleteDialog, OptionsDialog, DownloadProgressDialog
from idm_gui.theme import THEME
from idm_core.engine import DownloadEngine


@pytest.fixture(scope="module")
def tk_root():
    try:
        root = tk.Tk()
        root.withdraw()
        yield root
        root.destroy()
    except Exception:
        pytest.skip("Tkinter display not available")


def test_download_complete_dialog_modern_theme(tk_root):
    dlg = DownloadCompleteDialog(
        parent=tk_root,
        title="Sample_Video.mp4",
        output_path="C:/Downloads/Sample_Video.mp4",
        total_bytes=1024 * 1024 * 25,
    )
    # Check background color is surface dark
    assert dlg.top.cget("bg") == THEME["surface"]
    assert hasattr(dlg, "btn_open")
    assert hasattr(dlg, "btn_folder")
    assert hasattr(dlg, "btn_done")
    dlg.close()


def test_options_dialog_modern_theme(tk_root):
    dlg = OptionsDialog(parent=tk_root)
    assert dlg.top.cget("bg") == THEME["surface"]
    assert hasattr(dlg, "btn_save")
    assert hasattr(dlg, "btn_cancel")
    dlg.top.destroy()


def test_engine_granular_per_thread_progress_callback():
    engine = DownloadEngine()
    snapshots = []

    def part_callback(snapshot: list[dict]):
        snapshots.append(snapshot)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test_granular.bin")
        res = engine.download(
            "https://raw.githubusercontent.com/python/cpython/main/LICENSE",
            out_file,
            num_parts=4,
            part_progress_callback=part_callback,
        )
        assert res.success is True
        assert len(snapshots) > 0
        last_snap = snapshots[-1]
        assert len(last_snap) == 4
        assert all("id" in p and "downloaded" in p for p in last_snap)


def test_download_progress_dialog_interactive_tabs(tk_root):
    dlg = DownloadProgressDialog(
        parent=tk_root,
        task_id="t_adv",
        url="https://example.com/movie.mp4",
        output_path="C:/Downloads/movie.mp4",
        total_bytes=1024 * 1024 * 100,
        parts=4,
    )

    # Check tab frames exist
    assert hasattr(dlg, "tab1_frame")
    assert hasattr(dlg, "tab2_frame")
    assert hasattr(dlg, "tab3_frame")

    # Switch to Speed Limiter tab
    dlg._switch_tab(2)
    assert dlg.active_tab == 2
    assert hasattr(dlg, "speed_limit_enabled_var")
    assert hasattr(dlg, "speed_limit_val_var")

    # Switch to On-completion tab
    dlg._switch_tab(3)
    assert dlg.active_tab == 3
    assert hasattr(dlg, "cb_auto_close_var")
    assert hasattr(dlg, "cb_shutdown_var")

    # Switch back to Status tab
    dlg._switch_tab(1)
    assert dlg.active_tab == 1
    dlg.close()
