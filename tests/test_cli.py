import pytest
from unittest.mock import patch, MagicMock
from idm_clone.cli import build_parser, run_cli


def test_cli_parser_download_arguments():
    parser = build_parser()
    args = parser.parse_args(["download", "https://example.com/file.zip", "-o", "my_file.zip", "-p", "8"])
    assert args.command == "download"
    assert args.url == "https://example.com/file.zip"
    assert args.output == "my_file.zip"
    assert args.parts == 8


def test_cli_parser_stream_arguments():
    parser = build_parser()
    args = parser.parse_args(["stream", "https://example.com/video.m3u8", "-o", "video.ts"])
    assert args.command == "stream"
    assert args.url == "https://example.com/video.m3u8"
    assert args.output == "video.ts"


def test_cli_parser_broker_arguments():
    parser = build_parser()
    args = parser.parse_args(["broker"])
    assert args.command == "broker"


@patch("idm_clone.cli.DownloadEngine")
def test_run_cli_download_command(mock_engine_cls):
    mock_instance = MagicMock()
    mock_instance.probe.return_value = (1024, True)
    mock_instance.download.return_value.success = True
    mock_instance.download.return_value.bytes_downloaded = 1024
    mock_instance.download.return_value.output_path = "test.bin"
    mock_engine_cls.return_value = mock_instance

    code = run_cli(["download", "https://example.com/test.bin", "-o", "test.bin", "-p", "4"])
    assert code == 0
    mock_instance.download.assert_called_once()
