import os
import tkinter as tk
import pytest

from idm_gui.dialogs import DownloadInfoDialog, DialogAction, format_size_id


@pytest.fixture(scope="module")
def tk_root():
    try:
        root = tk.Tk()
        root.withdraw()
        yield root
        root.destroy()
    except Exception:
        pytest.skip("Tkinter display not available in this test runner environment")


def test_format_size_id():
    assert "B" in format_size_id(500)
    assert "KB" in format_size_id(1024 * 50)
    assert "337,84 MB" == format_size_id(int(337.84 * 1024 * 1024))


def test_download_info_dialog_ui(tk_root):
    url = "https://rr1---sn-2uuxa3vh-wvbes.googlevideo.com/videoplayback?expire="
    title = "PODKESMAS - OMESH DI TURKI BAWA 2 KOPE.mp4"

    dlg = DownloadInfoDialog(
        parent=tk_root,
        url=url,
        title=title,
        probed_size=int(337.84 * 1024 * 1024),
        category="Musik",
    )

    assert dlg.url == url
    assert dlg.title == title
    assert dlg.category == "Musik"
    assert dlg.action == DialogAction.CANCEL
    assert "Music" in dlg.path_var.get() or "Musik" in dlg.path_var.get()

    # Test Unduh Nanti
    dlg._on_later()
    assert dlg.action == DialogAction.LATER


def test_download_info_dialog_remember_category_path(tk_root):
    from idm_gui.settings import settings

    custom_dir = os.path.join(os.path.expanduser("~"), "Downloads", "CustomMovieFolder")
    custom_target = os.path.join(custom_dir, "my_movie.mp4")

    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/movie.mp4",
        title="my_movie.mp4",
        category="Video",
    )

    # User modifies path and checks remember box
    dlg.path_var.set(custom_target)
    dlg.remember_var.set(True)

    dlg._on_start()
    assert dlg.action == DialogAction.START

    # Verify that the category path is now remembered in settings!
    assert settings.get_category_path("Video") == os.path.abspath(custom_dir)

    # Next download dialog for 'Video' must automatically use this custom folder!
    dlg2 = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/another_movie.mp4",
        title="another_movie.mp4",
        category="Video",
    )
    assert os.path.dirname(dlg2.output_path) == os.path.abspath(custom_dir)
    dlg2.top.destroy()


def test_download_info_dialog_browse_folder_button(tk_root, monkeypatch):
    from idm_gui.settings import settings
    from tkinter import filedialog

    browsed_dir = os.path.join(os.path.expanduser("~"), "Downloads", "BrowsedFolderTest")
    # Mock askdirectory to simulate user clicking [...] and picking a folder
    monkeypatch.setattr(filedialog, "askdirectory", lambda **kwargs: browsed_dir)

    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/browse_test.mp4",
        title="browse_test.mp4",
        category="Program",
    )

    # Click [...]
    dlg._on_browse()

    # Verify that path_var has the new folder, but NOT yet saved to settings because checkbox is False
    assert os.path.dirname(dlg.path_var.get()) == os.path.abspath(browsed_dir)
    assert dlg.remember_var.get() is False

    # Check remember box and start download
    dlg.remember_var.set(True)
    dlg._on_start()

    # Now verify settings are updated
    assert settings.get_category_path("Program") == os.path.abspath(browsed_dir)


def test_download_info_dialog_cancel_calls_callback(tk_root):
    from idm_gui.dialogs import DownloadInfoDialog, DialogAction

    actions_received = []

    def handle_action(action, url, path, parts):
        actions_received.append(action)

    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/cancel_test.mp4",
        title="cancel_test.mp4",
        category="Video",
        on_action=handle_action,
    )

    # Click Batal
    dlg._on_cancel()

    assert len(actions_received) == 1
    assert actions_received[0] == DialogAction.CANCEL


def test_uncheck_remember_path_does_not_save_to_settings(tk_root, monkeypatch):
    from idm_gui.settings import settings
    from tkinter import filedialog

    # Reset any cached entry for 'Umum'
    if "category_paths" in settings.data and "Umum" in settings.data["category_paths"]:
        del settings.data["category_paths"]["Umum"]
        settings._save()

    # Original default path for 'Umum'
    initial_path = settings.get_category_path("Umum")

    temp_folder = os.path.join(os.path.expanduser("~"), "Downloads", "TempOneTimeOnlyFolder")
    monkeypatch.setattr(filedialog, "askdirectory", lambda **kwargs: temp_folder)

    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/photo.jpg",
        title="photo.jpg",
        category="Umum",
    )

    # User browses to temp_folder
    dlg._on_browse()
    assert os.path.dirname(dlg.path_var.get()) == os.path.abspath(temp_folder)

    # User DOES NOT check or unchecks the checkbox
    dlg.remember_var.set(False)

    # User clicks Start Download
    dlg._on_start()

    # Verify that the category path was NOT remembered!
    assert settings.get_category_path("Umum") == initial_path
    assert settings.get_category_path("Umum") != os.path.abspath(temp_folder)

    # Next download dialog for 'Umum' should still open in initial_path, NOT temp_folder!
    dlg2 = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/another_photo.jpg",
        title="another_photo.jpg",
        category="Umum",
    )
    assert os.path.dirname(dlg2.output_path) == initial_path
    dlg2.top.destroy()


def test_download_info_dialog_displays_native_app_icon(tk_root):
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/movie.mp4",
        title="movie.mp4",
        category="Video",
    )
    assert hasattr(dlg, "icon_label")
    assert dlg.icon_label.cget("image") != ""
    dlg.top.destroy()



