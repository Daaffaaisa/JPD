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


def test_download_info_dialog_probing_state_and_update(tk_root):
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/largefile.iso",
        title="largefile.iso",
        probed_size=0,
        category="Program",
        is_probing=True,
    )
    assert dlg.lbl_size.cget("text") == "Memeriksa ukuran..."
    assert dlg.is_probing is True

    dlg.update_probed_size(1024 * 1024 * 50)
    assert dlg.probed_size == 1024 * 1024 * 50
    assert dlg.lbl_size.cget("text") == "50,00 MB"
    assert dlg.is_probing is False
    dlg.top.destroy()


def test_download_info_dialog_connection_label_reflects_settings(tk_root):
    from idm_gui.settings import settings
    orig = settings.get_max_connections()
    try:
        settings.set_max_connections(16)
        dlg16 = DownloadInfoDialog(
            parent=tk_root,
            url="https://example.com/file16.iso",
            title="file16.iso",
        )
        assert "16 Koneksi" in dlg16.conn_label.cget("text")
        dlg16.top.destroy()

        settings.set_max_connections(32)
        dlg32 = DownloadInfoDialog(
            parent=tk_root,
            url="https://example.com/file32.iso",
            title="file32.iso",
        )
        assert "32 Koneksi" in dlg32.conn_label.cget("text")
        dlg32.top.destroy()
    finally:
        settings.set_max_connections(orig)


def test_download_info_dialog_add_category_button(tk_root, monkeypatch):
    from tkinter import simpledialog
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/file_cat.iso",
        title="file_cat.iso",
    )
    assert hasattr(dlg, "btn_add_cat")
    assert dlg.btn_add_cat.cget("command") != ""

    monkeypatch.setattr(simpledialog, "askstring", lambda *args, **kwargs: "Ebook")
    dlg._on_add_category()

    assert "Ebook" in dlg.cat_cb["values"]
    assert dlg.cat_var.get() == "Ebook"
    dlg.top.destroy()


def test_download_info_dialog_no_row5_overlap(tk_root):
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/movie.mp4",
        title="movie.mp4",
        category="Video",
    )
    assert hasattr(dlg, "info_frame")
    assert hasattr(dlg, "btn_frame")
    # Verify that info_frame and btn_frame do not collide on the same grid row
    info_row = int(dlg.info_frame.grid_info()["row"])
    btn_row = int(dlg.btn_frame.grid_info()["row"])
    assert info_row != btn_row
    assert btn_row > info_row
    dlg.top.destroy()


def test_download_info_dialog_resizable_for_high_dpi(tk_root):
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://example.com/movie.mp4",
        title="movie.mp4",
        category="Video",
    )
    # Check that minimum size is defined for High-DPI
    min_w, min_h = dlg.top.minsize()
    assert min_w >= 540
    assert min_h >= 340
    dlg.top.destroy()


def test_download_info_dialog_stream_placeholder_when_size_undetected(tk_root):
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://www.tiktok.com/@user/video/7685233045418298655",
        title="TikTok_Video_7685233045418298655.mp4",
        category="Video",
        probed_size=0,
    )
    # When size is not yet detected, placeholder appears
    assert bool(dlg.lbl_size.pack_info()) is True
    assert dlg.lbl_size.cget("text") == "Stream HD (1080p MP4)"
    dlg.top.destroy()


def test_download_info_dialog_stream_size_replaces_placeholder_when_probed(tk_root):
    dlg = DownloadInfoDialog(
        parent=tk_root,
        url="https://www.tiktok.com/@user/video/7685233045418298655",
        title="TikTok_Video_7685233045418298655.mp4",
        category="Video",
        probed_size=0,
    )
    assert dlg.lbl_size.cget("text") == "Stream HD (1080p MP4)"

    # When size is probed and available (> 0), real size replaces placeholder!
    dlg.update_probed_size(783403)
    assert bool(dlg.lbl_size.pack_info()) is True
    assert dlg.lbl_size.cget("text") == "765,04 KB"

    # If updated with 0 or undetected, it keeps placeholder
    dlg.update_probed_size(0)
    assert dlg.lbl_size.cget("text") == "Stream HD (1080p MP4)"
    dlg.top.destroy()



