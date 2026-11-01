import os


def test_standalone_executable_exists():
    root_exe = os.path.abspath("JustPressDownload.exe")
    dist_exe = os.path.abspath("dist/JustPressDownload.exe")
    assert (
        os.path.exists(root_exe) or os.path.exists(dist_exe)
    ), "JustPressDownload.exe must exist"

    target_exe = root_exe if os.path.exists(root_exe) else dist_exe
    # Check that file size is reasonable for a bundled app (> 15 MB)
    size_mb = os.path.getsize(target_exe) / (1024 * 1024)
    assert size_mb > 15, f"Executable too small: {size_mb} MB"


def test_main_app_entrypoint_exists():
    entry_path = os.path.abspath("main_app.py")
    assert os.path.exists(entry_path)
    with open(entry_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "from idm_gui.app import main" in content
