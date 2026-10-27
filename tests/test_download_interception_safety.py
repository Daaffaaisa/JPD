import pytest
import tkinter as tk

from idm_gui.dialogs import DownloadInfoDialog, DialogAction


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_double_extension_adware_detection():
    from idm_gui.app import IDMGUIApp
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    app = IDMGUIApp(root)

    # Suspicious file: document.pdf.exe
    suspicious, warning = app._check_file_security("document.pdf.exe")
    assert suspicious is True
    assert "ekstensi ganda" in warning.lower()

    # Normal file: setup.exe or archive.zip
    suspicious_safe, _ = app._check_file_security("setup.exe")
    assert suspicious_safe is False

    suspicious_safe_zip, _ = app._check_file_security("data.backup.tar.gz")
    assert suspicious_safe_zip is False

    app._on_close()


def test_download_info_dialog_shows_security_warning(tk_root):
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://scam-site.example/invoice.pdf.exe",
        title="invoice.pdf.exe",
        category="Program",
        is_suspicious=True,
        security_warning="Peringatan: Berkas memiliki ekstensi ganda (.pdf.exe)!",
    )

    assert hasattr(dlg, "lbl_security_warning")
    assert dlg.lbl_security_warning is not None
    assert "Peringatan" in dlg.lbl_security_warning.cget("text")
    dlg.top.destroy()
