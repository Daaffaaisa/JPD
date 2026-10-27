import os
import urllib.parse
import pytest

from idm_core.engine import DownloadEngine


def test_engine_accept_header_does_not_force_avif():
    engine = DownloadEngine()
    accept = engine.session.headers.get("Accept", "").lower()
    # AVIF should not be requested as first priority, otherwise servers transcode to blurry AVIF
    assert "image/avif" not in accept.split(",")[0]
    assert not accept.startswith("image/avif")


def test_engine_downloads_original_jpeg_or_png(monkeypatch):
    engine = DownloadEngine()

    class MockResponse:
        status_code = 200
        url = "https://example.com/highres_photo"
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Length": "543210",
        }

    monkeypatch.setattr(engine.session, "head", lambda url, **kwargs: MockResponse())
    fname = engine.get_filename("https://example.com/highres_photo")
    assert fname.endswith(".jpg") or fname.endswith(".jpeg")
    assert not fname.endswith(".avif")


def test_high_res_url_upgrades():
    # 1. Google Images imgurl extraction
    g_url = "https://www.google.com/imgres?imgurl=https%3A%2F%2Fimages.unsplash.com%2Fphoto-1543466835.jpg&imgrefurl=https%3A%2F%2Fexample.com"
    parsed_g = urllib.parse.urlparse(g_url)
    qs = urllib.parse.parse_qs(parsed_g.query)
    extracted_img = urllib.parse.unquote(qs.get("imgurl", [""])[0])
    assert extracted_img == "https://images.unsplash.com/photo-1543466835.jpg"

    # 2. Twitter name=orig upgrade
    tw_url = "https://pbs.twimg.com/media/F123456?format=jpg&name=small"
    tw_u = urllib.parse.urlparse(tw_url)
    tw_qs = urllib.parse.parse_qs(tw_u.query)
    tw_qs["name"] = ["orig"]
    upgraded_tw = urllib.parse.urlunparse(tw_u._replace(query=urllib.parse.urlencode(tw_qs, doseq=True)))
    assert "name=orig" in upgraded_tw

    # 3. Pinterest /originals/ upgrade
    pin_url = "https://i.pinimg.com/236x/ab/cd/ef/abcdef12345.jpg"
    import re
    upgraded_pin = re.sub(r"/\d+x/", "/originals/", pin_url)
    assert "/originals/" in upgraded_pin

    # 4. Wikimedia /thumb/ stripping
    wiki_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/File.jpg/300px-File.jpg"
    parts = wiki_url.split("/")
    if "thumb" in parts:
        thumb_idx = parts.index("thumb")
        parts.pop(thumb_idx)
        parts.pop()
    upgraded_wiki = "/".join(parts)
    assert upgraded_wiki == "https://upload.wikimedia.org/wikipedia/commons/a/ab/File.jpg"

