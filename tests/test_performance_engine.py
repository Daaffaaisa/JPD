import os
import tempfile
import pytest

from idm_core.engine import DownloadEngine, DownloadResult


def test_engine_has_high_throughput_connection_pool():
    engine = DownloadEngine()
    # Ensure connection pool has at least 32 connections for high concurrency
    adapter = engine.session.get_adapter("https://example.com")
    assert adapter._pool_connections >= 32
    assert adapter._pool_maxsize >= 32


def test_engine_direct_range_write_without_temp_merge_32_parts():
    engine = DownloadEngine()

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "direct_write_32.bin")
        # Download multi-part range using 32 parts like IDM max mode
        res = engine.download(
            "https://raw.githubusercontent.com/python/cpython/main/LICENSE",
            out_file,
            num_parts=32,
        )

        assert res.success is True
        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) == res.bytes_downloaded
        with open(out_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            assert "PYTHON SOFTWARE FOUNDATION" in content


def test_engine_uses_known_size_without_probing():
    engine = DownloadEngine()
    # Mock probe to ensure it is NOT called when known_size is provided
    probe_called = []
    def fake_probe(url, headers=None):
        probe_called.append(url)
        return 100, True

    engine.probe = fake_probe

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "known_size.bin")
        res = engine.download(
            "https://raw.githubusercontent.com/python/cpython/main/LICENSE",
            out_file,
            num_parts=4,
            known_size=1000,
        )
        assert len(probe_called) == 0  # Probe was skipped!


