import os
import pytest
from idm_gui.icon_utils import get_extension_icon_image


def test_get_extension_icon_image_returns_image_for_video():
    # .mp4 should return a valid PIL image (such as VLC or default Windows media icon)
    img = get_extension_icon_image(".mp4")
    assert img is not None
    assert img.size == (32, 32)
    assert img.mode == "RGBA"


def test_get_extension_icon_image_returns_image_for_zip():
    img = get_extension_icon_image("archive.zip")
    assert img is not None
    assert img.size == (32, 32)


def test_get_extension_icon_image_fallback():
    # Empty or unknown extension should return a fallback icon, never None
    img = get_extension_icon_image("")
    assert img is not None
    assert img.size == (32, 32)
