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
