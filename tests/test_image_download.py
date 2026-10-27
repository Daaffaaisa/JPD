import os
import tempfile
import pytest

from idm_core.engine import DownloadEngine
from idm_gui.settings import SettingsManager


def test_engine_detects_image_extension_from_mime_type(monkeypatch):
    engine = DownloadEngine()

    class MockResponse:
        status_code = 200
        url = "https://images.example.com/media/pic-without-ext"
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Length": "12345",
        }

    monkeypatch.setattr(engine.session, "head", lambda url, **kwargs: MockResponse())

    fname = engine.get_filename("https://images.example.com/media/pic-without-ext")
    assert fname.endswith(".jpg") or fname.endswith(".jpeg")


def test_engine_detects_image_extension_from_query_params(monkeypatch):
    engine = DownloadEngine()

    # Query param ?format=png
    fname = engine.get_filename("https://pbs.example.com/media/F123456?format=png&name=large")
    assert fname.endswith(".png")


def test_app_detects_gambar_category_and_does_not_append_mp4():
    import tkinter as tk
    from idm_gui.app import IDMGUIApp

    root = tk.Tk()
    root.withdraw()
    app = IDMGUIApp(root)

    cat = app._detect_category("https://example.com/photo.jpg", "Foto Pemandangan")
    assert cat == "Gambar"

    # Verify helper does not turn image into .mp4
    title = app._get_clean_title_with_ext("https://example.com/photo.jpg", "Foto Pemandangan", cat)
    assert not title.endswith(".mp4")
    assert title.endswith(".jpg") or title.endswith(".jpeg")

    app._on_close()
