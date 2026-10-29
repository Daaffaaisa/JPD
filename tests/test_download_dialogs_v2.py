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
    assert hasattr(dlg, "btn_open")
    assert hasattr(dlg, "btn_folder")
    assert hasattr(dlg, "btn_done")
    assert dlg.btn_open.cget("text") == "Buka Berkas"
    dlg.close()


def test_download_progress_dialog_functional_tabs(tk_root):
    dlg = DownloadProgressDialog(
        parent=tk_root,
        task_id="t_tab_test",
        url="https://example.com/file.bin",
        output_path="C:\\test\\file.bin",
    )
    assert hasattr(dlg, "lbl_tab2")
    assert hasattr(dlg, "lbl_tab3")
    assert "Pembatas Kecepatan" in dlg.lbl_tab2.cget("text")
    assert "Opsi saat selesai" in dlg.lbl_tab3.cget("text")
    assert dlg.lbl_tab2.cget("cursor") == "hand2"
    assert dlg.lbl_tab3.cget("cursor") == "hand2"

    # Test clicking Tab 2 & Tab 3
    dlg._switch_tab(2)
    assert dlg.active_tab == 2
    dlg._switch_tab(3)
    assert dlg.active_tab == 3
    dlg._switch_tab(1)
    assert dlg.active_tab == 1
    dlg.close()


def test_download_progress_dialog_uses_coords_without_delete_all(tk_root, monkeypatch):
    dlg = DownloadProgressDialog(
        parent=tk_root,
        task_id="t_coords_test",
        url="https://example.com/file.iso",
        output_path="C:\\test\\file.iso",
        total_bytes=1024 * 1024 * 80,
        parts=4,
    )

    # Track calls to delete on seg_canvas
    delete_called = []
    original_delete = dlg.seg_canvas.delete
    monkeypatch.setattr(dlg.seg_canvas, "delete", lambda *a, **kw: delete_called.append(a))

    # Trigger update_progress
    dlg.update_progress(
        bytes_downloaded=1024 * 1024 * 40,
        total_bytes=1024 * 1024 * 80,
        speed_bps=1024 * 1024 * 8,
    )

    # Verify that delete("all") was NOT called during update_progress
    assert "all" not in delete_called
    assert len(delete_called) == 0

    # Verify persistent segment items exist
    assert hasattr(dlg, "seg_fill_rects")
    assert len(dlg.seg_fill_rects) == dlg.parts

    dlg.close()
