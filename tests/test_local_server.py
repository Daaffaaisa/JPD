import json
import time
import requests
import pytest

from idm_server.server import LocalDownloadServer
from idm_scheduler.queue import DownloadQueue


@pytest.fixture(scope="module")
def local_server():
    queue = DownloadQueue()
    server = LocalDownloadServer(host="127.0.0.1", port=0, queue=queue)
    server.start()
    port = server.port
    yield f"http://127.0.0.1:{port}", queue
    server.stop()


def test_server_ping_endpoint_with_cors(local_server):
    base_url, _ = local_server
    resp = requests.get(f"{base_url}/api/ping", timeout=3)
    
    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
    data = resp.json()
    assert data.get("status") == "ok"
    assert "idm" in data.get("app", "").lower()


def test_server_download_endpoint_adds_task_to_queue(local_server):
    base_url, queue = local_server
    payload = {
        "url": "https://example.com/test_video.mp4",
        "title": "Cool Video",
        "parts": 4
    }
    resp = requests.post(
        f"{base_url}/api/download",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=3
    )
    
    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
    data = resp.json()
    assert data.get("status") == "ok"
    task_id = data.get("taskId")
    assert task_id is not None
    
    # Verify task in queue
    task = queue.get_task(task_id)
    assert task is not None
    assert task.url == payload["url"]


def test_server_options_preflight_cors(local_server):
    base_url, _ = local_server
    resp = requests.options(f"{base_url}/api/download", timeout=3)
    
    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
    assert "POST" in resp.headers.get("Access-Control-Allow-Methods", "")
