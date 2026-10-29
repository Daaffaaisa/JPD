import os
import pytest
import tkinter as tk
from unittest.mock import MagicMock
from idm_gui.dialogs import DownloadCompleteDialog, OptionsDialog
from idm_gui.theme import THEME


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_download_complete_dialog_modern_ui(tk_root):
    dlg = DownloadCompleteDialog(
        parent=tk_root,
        title="Sample_Video_4K.mp4",
        output_path="C:/Downloads/Sample_Video_4K.mp4",
        total_bytes=1024 * 1024 * 150,
    )

    assert dlg.top is not None
    assert dlg.top.cget("bg") == THEME["surface"]
    assert hasattr(dlg, "btn_open")
    assert hasattr(dlg, "btn_folder")
    assert hasattr(dlg, "btn_done")

    # Verify buttons have rounded modern callbacks and labels
    assert dlg.btn_open.cget("text") == "Buka Berkas"
    assert dlg.btn_folder.cget("text") == "Buka Folder"
    assert dlg.btn_done.cget("text") == "Selesai"

    dlg.close()


def test_options_dialog_theme_tokens_and_notebook(tk_root):
    dlg = OptionsDialog(parent=tk_root)

    assert dlg.top is not None
    assert dlg.top.cget("bg") == THEME["surface"]
    assert hasattr(dlg, "notebook")
    assert len(dlg.notebook.tabs()) == 4

    # Check that browse buttons exist as modern buttons
    assert hasattr(dlg, "btn_browse")
    assert hasattr(dlg, "btn_temp_browse")
    assert hasattr(dlg, "btn_save")
    assert hasattr(dlg, "btn_cancel")

    dlg.top.destroy()
