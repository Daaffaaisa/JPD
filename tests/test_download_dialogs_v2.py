import os
import tkinter as tk
import pytest

from idm_gui.dialogs import (
    DownloadProgressDialog,
    DownloadCompleteDialog,
    format_size_id,
    format_time_left,
)


@pytest.fixture(scope="module")
def tk_root():
    try:
        root = tk.Tk()
        root.withdraw()
        yield root
        root.destroy()
    except Exception:
        pytest.skip("Tkinter display not available in this test runner environment")


def test_format_time_left():
    assert format_time_left(0) == "Selesai"
    assert "detik" in format_time_left(45)
    assert "13 menit 58 detik" == format_time_left(13 * 60 + 58)
    assert "1 jam" in format_time_left(3600 + 120)


def test_download_progress_dialog_ui(tk_root):
    dlg = DownloadProgressDialog(
        parent=tk_root,
        task_id="t123",
        url="https://tunnel5.dlproxy.uk/download/game.zip",
        output_path="C:\\Users\\test\\Downloads\\game.zip",
        total_bytes=1024 * 1024 * 100,  # 100 MB
        parts=4,
    )

    assert dlg.task_id == "t123"
    assert dlg.parts == 4
    assert dlg.top is not None

    # Test updating progress
    dlg.update_progress(
        bytes_downloaded=1024 * 1024 * 25,
        total_bytes=1024 * 1024 * 100,
        speed_bps=1024 * 1024 * 5,  # 5 MB/s
        part_progress=[
            {"id": 1, "downloaded": 1024 * 1024 * 10, "status": "Menerima data..."},
            {"id": 2, "downloaded": 1024 * 1024 * 5, "status": "Menerima data..."},
            {"id": 3, "downloaded": 1024 * 1024 * 5, "status": "Menerima data..."},
            {"id": 4, "downloaded": 1024 * 1024 * 5, "status": "Menerima data..."},
        ],
    )

    dlg.close()


def test_download_complete_dialog_ui(tk_root):
    dlg = DownloadCompleteDialog(
        parent=tk_root,
        title="We-Were-Here-Tomorrow-AnkerGames.zip",
        output_path="C:\\Downloads\\game.zip",
        total_bytes=1024 * 1024 * 50,
    )

    assert dlg.title == "We-Were-Here-Tomorrow-AnkerGames.zip"
    assert dlg.top is not None
    dlg.close()


def test_download_progress_dialog_disabled_tabs(tk_root):
    dlg = DownloadProgressDialog(
        parent=tk_root,
        task_id="t_tab_test",
        url="https://example.com/file.bin",
        output_path="C:\\test\\file.bin",
    )
    assert hasattr(dlg, "lbl_tab2")
    assert hasattr(dlg, "lbl_tab3")
    assert "Segera Hadir" in dlg.lbl_tab2.cget("text")
    assert "Segera Hadir" in dlg.lbl_tab3.cget("text")
    assert dlg.lbl_tab2.cget("cursor") in ("arrow", "")
    assert dlg.lbl_tab3.cget("cursor") in ("arrow", "")
    dlg.close()
