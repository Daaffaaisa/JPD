import os
import subprocess
import pytest


def test_content_js_blacklist_storage_and_filter_logic():
    """Verify content.js contains blacklist storage schema and isSiteOrPageBlocked logic."""
    content_js_path = os.path.abspath("extension/content.js")
    assert os.path.exists(content_js_path)

    with open(content_js_path, "r", encoding="utf-8") as f:
        code = f.read()

    # JS syntax must be valid
    res = subprocess.run(["node", "-c", content_js_path], capture_output=True, text=True)
    assert res.returncode == 0, f"JS Syntax Error: {res.stderr}"

    # Verify keys for domain and page blacklist and session dismissal
    assert "jpd_blacklist_domains" in code, "Must support jpd_blacklist_domains"
    assert "jpd_blacklist_pages" in code, "Must support jpd_blacklist_pages"
    assert "jpd_session_dismissed" in code, "Must support jpd_session_dismissed in sessionStorage"

    # Verify filter function
    assert "isSiteOrPageBlocked" in code, "Must define isSiteOrPageBlocked function"
    assert "sessionStorage" in code, "Must check sessionStorage"


def test_content_js_mini_popover_and_dismiss_options():
    """Verify content.js contains close button, 3-option mini popover, and toast feedback."""
    content_js_path = os.path.abspath("extension/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Close button and popover container
    assert "jpd-close-btn" in code, "Must have jpd-close-btn element"
    assert "jpd-dismiss-popover" in code, "Must have jpd-dismiss-popover element"

    # 3 Specific options
    assert "jpd-opt-session" in code, "Must have session dismissal option"
    assert "jpd-opt-page" in code, "Must have page blacklist option"
    assert "jpd-opt-domain" in code, "Must have domain blacklist option"

    # Multi-language keys
    assert "dismiss_session" in code, "Must have dismiss_session i18n string"
    assert "dismiss_page" in code, "Must have dismiss_page i18n string"
    assert "dismiss_domain" in code, "Must have dismiss_domain i18n string"
    assert "toast_dismissed_session" in code, "Must have session toast string"
    assert "toast_dismissed_domain" in code, "Must have domain toast string"


def test_popup_html_and_js_site_exclusion_controls():
    """Verify popup.html and popup.js contain domain quick-toggle and exclusion accordion."""
    popup_html_path = os.path.abspath("extension/popup.html")
    popup_js_path = os.path.abspath("extension/popup.js")

    with open(popup_html_path, "r", encoding="utf-8") as f:
        html = f.read()
    with open(popup_js_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Syntax test
    res = subprocess.run(["node", "-c", popup_js_path], capture_output=True, text=True)
    assert res.returncode == 0, f"Popup JS Syntax error: {res.stderr}"

    # HTML elements
    assert "siteToggleSection" in html, "Must have siteToggleSection"
    assert "siteDomainLabel" in html, "Must have siteDomainLabel"
    assert "siteToggleSwitch" in html, "Must have siteToggleSwitch"
    assert "exclusionAccordionHeader" in html, "Must have exclusionAccordionHeader"
    assert "exclusionCount" in html, "Must have exclusionCount badge"
    assert "exclusionList" in html, "Must have exclusionList accordion body"
    assert "exclusionItems" in html, "Must have exclusionItems container"

    # JS logic
    assert "jpd_blacklist_domains" in code, "Must read/write jpd_blacklist_domains"
    assert "jpd_blacklist_pages" in code, "Must read/write jpd_blacklist_pages"
    assert "jpd_unblock_and_show" in code, "Must dispatch jpd_unblock_and_show live signal"
    assert "exclusion_badge_site" in code, "Must support localized exclusion_badge_site"
    assert "exclusion_badge_page" in code, "Must support localized exclusion_badge_page"


def test_content_js_live_unblock_message_listener():
    """Verify content.js listens for jpd_unblock_and_show and clears session dismissal."""
    content_js_path = os.path.abspath("extension/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "jpd_unblock_and_show" in code, "content.js must handle jpd_unblock_and_show message"
    assert "chrome.runtime.onMessage.addListener" in code, "content.js must register onMessage listener"
    assert "sessionStorage.removeItem" in code, "content.js must clear jpd_session_dismissed on unblock"



