import os
import subprocess
import pytest


def test_popup_html_contains_dark_tokens_and_accessibility():
    popup_path = os.path.abspath("extension/popup.html")
    assert os.path.exists(popup_path)

    with open(popup_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Checks for Midnight Slate & Sapphire tokens
    assert "#0f131d" in html
    assert "#2563eb" in html
    assert "#1b2230" in html

    # Checks for pulse animation and accessibility media query
    assert "prefers-reduced-motion" in html
    assert "pulseGreen" in html
    assert "status-dot" in html

    # Checks required functional IDs
    assert 'id="status"' in html
    assert 'id="urlInput"' in html
    assert 'id="downloadBtn"' in html


def test_popup_js_syntax():
    js_path = os.path.abspath("extension/popup.js")
    assert os.path.exists(js_path)

    # Validate JavaScript syntax with node -c
    res = subprocess.run(["node", "-c", js_path], capture_output=True, text=True)
    assert res.returncode == 0, f"JS Syntax error: {res.stderr}"

    with open(js_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "STRINGS" in code
    assert "jpd_language" in code
    assert "langToggleBtn" in code


def test_manifest_extension_name_and_locales():
    import json
    manifest_path = os.path.abspath("extension/manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["name"] == "JPD Integration Module"


def test_extension_dual_language_live_sync_and_prominent_toggle():
    """Verify popup has dedicated language selector card, and content.js synchronizes live."""
    popup_html_path = os.path.abspath("extension/popup.html")
    popup_js_path = os.path.abspath("extension/popup.js")
    content_js_path = os.path.abspath("extension/content.js")

    with open(popup_html_path, "r", encoding="utf-8") as f:
        html = f.read()
    with open(popup_js_path, "r", encoding="utf-8") as f:
        p_code = f.read()
    with open(content_js_path, "r", encoding="utf-8") as f:
        c_code = f.read()

    # 1. Popup HTML must have dedicated language card and buttons
    assert "lang-selector-card" in html, "Must have dedicated lang-selector-card"
    assert "lblLanguage" in html, "Must have lblLanguage label"
    assert "langBtnId" in html, "Must have langBtnId button"
    assert "langBtnEn" in html, "Must have langBtnEn button"

    # 2. Popup JS must handle both buttons and broadcast
    assert "langBtnId.addEventListener" in p_code, "Must attach click to langBtnId"
    assert "langBtnEn.addEventListener" in p_code, "Must attach click to langBtnEn"
    assert "jpd_set_language" in p_code, "Must broadcast jpd_set_language"
    assert "label_language" in p_code, "Must have label_language in STRINGS"

    # 3. Content JS must listen to jpd_set_language and storage changes, and update panel
    assert "jpd_set_language" in c_code, "content.js must handle jpd_set_language message"
    assert "updatePanelTexts" in c_code, "content.js must have updatePanelTexts function"
    assert "changes.jpd_language" in c_code, "content.js must listen for changes.jpd_language"

