import os
import pytest
from idm_gui.settings import settings


@pytest.fixture(autouse=True)
def isolate_test_settings(monkeypatch, tmp_path):
    """
    Guarantees that no test execution ever reads from or writes to the user's
    actual production settings in ~/.idm_clone/settings.json or tasks.json.
    """
    test_cfg_path = str(tmp_path / "test_settings.json")
    monkeypatch.setattr(settings, "config_path", test_cfg_path)
    monkeypatch.setattr(settings, "data", {
        "category_paths": {},
        "max_connections": 8,
        "browser_integration": {
            "chrome": True,
            "edge": True,
            "firefox": True,
            "opera": False,
        },
        "autorun_startup": False,
        "close_to_tray": True,
        "start_minimized": False,
        "play_sound_on_complete": False,
        "confirm_on_delete": True,
        "autoclose_progress": False,
        "monitor_clipboard": True,
        "file_types": "3GP 7Z AAC ACE AIF ARJ ASF AVI BIN BZ2 EXE GZ GZIP IMG ISO LZH M4A M4V MKV MOV MP3 MP4 MPA MPE MPEG MPG MSI MSU OGG OGV PDF PLJ PPS PPT PPTX QT R0* R1* RA RAR RPM SEA SIT SITX TAR TIF TIFF TXT WAV WMA WMV Z ZIP",
        "exceptions": "*.speedtest.net *.fast.com",
        "temp_dir": os.path.join(str(tmp_path), "Temp"),
    })
