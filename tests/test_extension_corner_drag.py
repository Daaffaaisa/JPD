import os
import subprocess


def test_content_js_corner_persistence_and_drag():
    content_js_path = os.path.abspath("extension/content.js")
    assert os.path.exists(content_js_path)

    with open(content_js_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Validate JavaScript syntax
    res = subprocess.run(["node", "-c", content_js_path], capture_output=True, text=True)
    assert res.returncode == 0, f"JS Syntax Error: {res.stderr}"

    # Verify corner persistence tokens
    assert "jpd_panel_corner" in code
    assert "preferredCorner" in code
    assert "chrome.storage.local" in code

    # Verify 4 corners supported
    assert "top-right" in code
    assert "top-left" in code
    assert "bottom-left" in code
    assert "bottom-right" in code

    # Verify drag handle and calculations
    assert "jpd-drag-handle" in code
    assert "getClosestCorner" in code
    assert "applyCornerPosition" in code
    assert "mousedown" in code
    assert "mousemove" in code
    assert "mouseup" in code

    # Verify active video persistence and YouTube Shorts & TikTok tracker
    assert "checkShortsAndVideos" in code
    assert "/shorts/" in code
    assert "syncPanelPosition" in code
    assert "Download dengan JPD" in code
    assert "tiktok.com" in code
    assert "getTikTokVideoUrl" in code
    assert "getTikTokVideoTitle" in code

    # Verify synchronous localStorage caching and zero-transition position jump elimination
    assert "localStorage.getItem" in code
    assert "localStorage.setItem" in code
    assert 'p.style.transition = "none"' in code


def test_manifest_storage_permission():
    manifest_path = os.path.abspath("extension/manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert '"storage"' in content, "Extension requires storage permission for corner preference"
