import argparse
import os
import sys
import tempfile
import urllib.parse
from typing import Optional
import requests

from idm_core.engine import DownloadEngine
from idm_media.parser import StreamParser
from idm_media.muxer import StreamMuxer
from idm_broker.broker import NativeMessageBroker
from idm_scheduler.queue import DownloadQueue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="idm-clone",
        description="High-performance multipart download manager mirroring IDM architecture",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: download
    dl_parser = subparsers.add_parser("download", help="Download a file using parallel HTTP Range chunks")
    dl_parser.add_argument("url", help="Target URL to download")
    dl_parser.add_argument("-o", "--output", help="Destination file path")
    dl_parser.add_argument("-p", "--parts", type=int, default=4, help="Number of concurrent parts (default: 4)")

    # Subcommand: stream
    stream_parser = subparsers.add_parser("stream", help="Parse and download streaming media (HLS .m3u8 / DASH .mpd)")
    stream_parser.add_argument("url", help="Target manifest URL (.m3u8 or .mpd)")
    stream_parser.add_argument("-o", "--output", help="Destination media file path (e.g. video.ts)")

    # Subcommand: broker
    subparsers.add_parser("broker", help="Run browser Native Messaging Host broker over stdio")

    return parser


def default_filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    name = os.path.basename(parsed.path)
    return name if name else "downloaded_file.bin"


def handle_download(url: str, output: Optional[str], parts: int) -> int:
    engine = DownloadEngine()
    out_path = output or default_filename_from_url(url)
    
    print(f"[*] Probing {url} ...")
    size, range_ok = engine.probe(url)
    print(f"[*] Size: {size} bytes | HTTP Range Support: {range_ok} | Connections: {parts if range_ok else 1}")

    result = engine.download(url, out_path, num_parts=parts)
    if result.success:
        print(f"[+] Download complete: {result.output_path} ({result.bytes_downloaded} bytes)")
        return 0
    else:
        print(f"[-] Download failed: {result.error}")
        return 1


def handle_stream(url: str, output: Optional[str]) -> int:
    out_path = output or "stream_output.ts"
    print(f"[*] Fetching stream manifest from {url} ...")
    
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    manifest_text = resp.text

    if ".mpd" in url.lower():
        segments = StreamParser.parse_mpd(manifest_text, base_url=url)
    else:
        segments = StreamParser.parse_m3u8(manifest_text, base_url=url)

    if not segments:
        print("[-] No media segments found in manifest.")
        return 1

    print(f"[*] Found {len(segments)} segments. Downloading segments ...")
    engine = DownloadEngine()
    muxer = StreamMuxer()
    
    with tempfile.TemporaryDirectory(prefix="idm_stream_") as tmpdir:
        seg_files = []
        for i, seg in enumerate(segments):
            seg_dest = os.path.join(tmpdir, f"seg_{i:04d}.tmp")
            res = engine.download(seg.url, seg_dest, num_parts=1)
            if not res.success:
                print(f"[-] Failed to download segment {i}: {res.error}")
                return 1
            seg_files.append(seg_dest)
        
        print(f"[*] Muxing and concatenating {len(seg_files)} segments ...")
        muxer.concat_segments(seg_files, out_path)
        print(f"[+] Stream successfully assembled into {out_path}!")
    return 0


def handle_broker() -> int:
    broker = NativeMessageBroker()
    queue = DownloadQueue()
    engine = DownloadEngine()

    while True:
        try:
            msg = broker.read_message()
            if msg is None:
                break
            response = broker.handle_command(msg, queue=queue, engine=engine)
            broker.write_message(msg=response)
        except (KeyboardInterrupt, BrokenPipeError):
            break
        except Exception as e:
            broker.write_message(msg={"status": "error", "error": str(e)})
    return 0


def run_cli(args: Optional[list[str]] = None) -> int:
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.command == "download":
        return handle_download(parsed_args.url, parsed_args.output, parsed_args.parts)
    elif parsed_args.command == "stream":
        return handle_stream(parsed_args.url, parsed_args.output)
    elif parsed_args.command == "broker":
        return handle_broker()
    return 0
