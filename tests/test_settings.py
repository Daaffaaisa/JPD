import os
import tempfile
import pytest

from idm_gui.settings import SettingsManager


def test_settings_manager_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "test_settings.json")
        sm = SettingsManager(config_path=cfg_file)

        # Default path when not remembered
        default_dir = os.path.join(tmpdir, "Downloads")
        video_path = sm.get_category_path("Video", default_base=default_dir)
        assert video_path == os.path.join(default_dir, "Video")


def test_settings_manager_remember_and_persist_category_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "test_settings.json")
        sm = SettingsManager(config_path=cfg_file)

        custom_video_dir = os.path.join(tmpdir, "MyCustomVideos")
        sm.set_category_path("Video", custom_video_dir)

        # Retrieve immediately
        assert sm.get_category_path("Video") == custom_video_dir

        # Reload from fresh instance to verify persistence on disk
        sm2 = SettingsManager(config_path=cfg_file)
        assert sm2.get_category_path("Video") == custom_video_dir


def test_settings_manager_max_connections():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "test_settings.json")
        sm = SettingsManager(config_path=cfg_file)

        # Default max connections (8, matching IDM standard)
        assert sm.get_max_connections() == 8

        # Set to 32
        sm.set_max_connections(32)
        assert sm.get_max_connections() == 32

        # Verify persistence on reload
        sm2 = SettingsManager(config_path=cfg_file)
        assert sm2.get_max_connections() == 32

