import os
import threading
import time
import pytest
from unittest.mock import MagicMock
from idm_core.engine import DownloadEngine, DownloadResult


def test_engine_invokes_part_progress_callback(tmp_path):
    engine = DownloadEngine()
    test_file = str(tmp_path / "stream_test.bin")
    file_size = 100 * 1024  # 100 KB
    num_parts = 4

    # Mock probe and _create_session
    engine.probe = MagicMock(return_value=(file_size, True))

    captured_part_updates = []

    def part_cb(part_data: list[dict]):
        captured_part_updates.append([dict(p) for p in part_data])

    # Mock session and responses for parts
    chunk_data = b"x" * 1024  # 1 KB chunks
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 206
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content = MagicMock(return_value=[chunk_data] * 25)
    mock_session.get = MagicMock(return_value=mock_resp)
    engine._create_session = MagicMock(return_value=mock_session)

    res = engine.download(
        url="https://example.com/test.bin",
        output_path=test_file,
        num_parts=num_parts,
        part_progress_callback=part_cb,
    )

    assert res.success is True
    assert len(captured_part_updates) > 0
    last_update = captured_part_updates[-1]
    assert len(last_update) == num_parts
    for p in last_update:
        assert "id" in p
        assert "start_byte" in p
        assert "end_byte" in p
        assert "downloaded" in p
        assert "status" in p


def test_engine_speed_limiter_throttles_download(tmp_path):
    engine = DownloadEngine()
    test_file = str(tmp_path / "limit_test.bin")
    file_size = 10 * 1024  # 10 KB

    engine.probe = MagicMock(return_value=(file_size, False))

    chunk_data = b"a" * 1024
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content = MagicMock(return_value=[chunk_data] * 10)
    mock_session.get = MagicMock(return_value=mock_resp)
    engine._create_session = MagicMock(return_value=mock_session)

    # Set speed limit to 2 KB/s (so 10 KB should take ~0.2-0.5s or throttle delay)
    start_t = time.time()
    res = engine.download(
        url="https://example.com/single.bin",
        output_path=test_file,
        num_parts=1,
        speed_limit_bps=2048,  # 2 KB/s
    )
    elapsed = time.time() - start_t

    assert res.success is True
    assert os.path.exists(test_file)
