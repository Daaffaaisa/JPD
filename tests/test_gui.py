import os
import unittest
from unittest.mock import MagicMock, patch

from idm_gui.app import format_bytes, IDMGUIApp


def test_format_bytes():
    assert format_bytes(500) == "500 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024 * 5) == "5.0 MB"
    assert format_bytes(1024 * 1024 * 1024 * 2) == "2.00 GB"


@patch("tkinter.Tk")
@patch("tkinter.ttk.Style")
def test_gui_app_initialization(mock_style, mock_tk):
    mock_root = MagicMock()
    app = IDMGUIApp(mock_root)
    
    assert app.root == mock_root
    assert app.queue is not None
    assert app.engine is not None
    mock_root.title.assert_called_with("Just Press Download")
    mock_root.after.assert_called()
