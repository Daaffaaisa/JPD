import os
import subprocess
import pytest


def test_popup_html_contains_segmented_language_toggle():
    """Verify popup.html contains a clear dual-language toggle switch (ID / EN)."""
    popup_html_path = os.path.abspath("extension/popup.html")
    with open(popup_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Must have segmented control container and buttons for ID and EN
    assert "langSwitchContainer" in html, "Must have langSwitchContainer for language toggle"
    assert "langBtnId" in html, "Must have langBtnId button"
    assert "langBtnEn" in html, "Must have langBtnEn button"
    assert "lang-segment" in html, "Must have lang-segment CSS styling"


def test_popup_js_language_toggle_and_sync():
    """Verify popup.js handles ID/EN toggle switch and broadcasts to tabs and server."""
    popup_js_path = os.path.abspath("extension/popup.js")
    with open(popup_js_path, "r", encoding="utf-8") as f:
        code = f.read()

    # JS syntax
    res = subprocess.run(["node", "-c", popup_js_path], capture_output=True, text=True)
    assert res.returncode == 0, f"JS Syntax Error: {res.stderr}"

    assert "langBtnId" in code, "popup.js must bind langBtnId"
    assert "langBtnEn" in code, "popup.js must bind langBtnEn"
    assert "setLanguage" in code, "popup.js must define setLanguage function"
    assert "jpd_set_language" in code, "popup.js must broadcast jpd_set_language to tabs"


def test_content_js_listens_to_language_change():
    """Verify content.js updates floating button texts on language change."""
    content_js_path = os.path.abspath("extension/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        code = f.read()

    # JS syntax
    res = subprocess.run(["node", "-c", content_js_path], capture_output=True, text=True)
    assert res.returncode == 0, f"JS Syntax Error: {res.stderr}"

    assert "jpd_set_language" in code, "content.js must handle jpd_set_language message"
    assert "updatePanelLanguage" in code, "content.js must define updatePanelLanguage function"


def test_server_handles_settings_language_update():
    """Verify local loopback server supports POST /api/settings with language."""
    server_py_path = os.path.abspath("src/idm_server/server.py")
    with open(server_py_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "/api/settings" in code, "server.py must support /api/settings endpoint"
