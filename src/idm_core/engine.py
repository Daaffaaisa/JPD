from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import shutil
import tempfile
import threading
import time
from typing import Callable, Optional
import requests
from requests.adapters import HTTPAdapter, Retry


@dataclass
class DownloadResult:
    success: bool
    bytes_downloaded: int
    num_parts: int
    output_path: str
    error: Optional[str] = None


class Non206RangeResponseError(Exception):
    pass


class DownloadEngine:
    """Core download engine supporting parallel chunked downloads via HTTP Range."""

    def _create_session(self) -> requests.Session:
        s = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=32,
            pool_maxsize=32,
            max_retries=Retry(
                total=2,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504],
            ),
        )
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        })
        return s

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or self._create_session()

    def get_filename(self, url: str) -> str:
        """Determines proper filename from Content-Disposition, URL path, query params, or MIME type."""
        import re
        import urllib.parse
        try:
            parsed = urllib.parse.urlparse(url)
            base = os.path.basename(parsed.path)

            # Check query params for explicit format or extension (common in Twitter, CDNs, etc.)
            qs = urllib.parse.parse_qs(parsed.query)
            query_ext = ""
            for k in ["format", "ext", "extension"]:
                if k in qs and qs[k][0]:
                    fmt = qs[k][0].lower().strip(".")
                    if fmt in ["jpg", "jpeg", "png", "webp", "gif", "svg", "avif", "mp4", "mp3", "pdf", "zip"]:
                        query_ext = f".{fmt}"
                        break

            resp = self.session.head(url, headers={"Accept-Encoding": "identity"}, allow_redirects=True, timeout=10)
            if resp.status_code >= 400:
                resp = self.session.get(url, headers={"Accept-Encoding": "identity"}, stream=True, allow_redirects=True, timeout=10)

            cd = resp.headers.get("Content-Disposition", "")
            if cd:
                m = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\r\n]+)["\']?', cd, re.IGNORECASE)
                if m:
                    name = urllib.parse.unquote(m.group(1).strip())
                    if name:
                        return os.path.basename(name)

            final_parsed = urllib.parse.urlparse(resp.url or url)
            final_base = os.path.basename(final_parsed.path) or base

            if final_base and "." in final_base:
                return urllib.parse.unquote(final_base)

            if query_ext:
                fname = final_base if final_base else "image"
                return f"{fname}{query_ext}"

            ct = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
            mime_map = {
                # Images
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif",
                "image/svg+xml": ".svg",
                "image/avif": ".avif",
                "image/bmp": ".bmp",
                "image/x-icon": ".ico",
                # Videos & Audio
                "video/mp4": ".mp4",
                "video/webm": ".webm",
                "video/x-matroska": ".mkv",
                "audio/mpeg": ".mp3",
                "audio/mp4": ".m4a",
                "audio/ogg": ".ogg",
                "audio/wav": ".wav",
                # Documents & Archives
                "application/zip": ".zip",
                "application/x-rar-compressed": ".rar",
                "application/x-7z-compressed": ".7z",
                "application/pdf": ".pdf",
            }
            ext = mime_map.get(ct, "")
            if final_base and ext:
                return f"{final_base}{ext}"
            elif ext:
                prefix = "image" if "image" in ct else "download"
                return f"{prefix}{ext}"
            return final_base if final_base else "download.bin"
        except Exception:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            base = os.path.basename(parsed.path)
            qs = urllib.parse.parse_qs(parsed.query)
            for k in ["format", "ext", "extension"]:
                if k in qs and qs[k][0]:
                    fmt = qs[k][0].lower().strip(".")
                    if fmt in ["jpg", "jpeg", "png", "webp", "gif", "svg", "avif", "mp4", "mp3", "pdf", "zip"]:
                        fname = base if base else "image"
                        return f"{fname}.{fmt}"
            return base if base else "download.bin"

    def probe(self, url: str, headers: Optional[dict] = None) -> tuple[int, bool]:
        """Probes the remote URL for Content-Length and Range support."""
        try:
            req_headers = {"Accept-Encoding": "identity"}
            if headers:
                req_headers.update(headers)
            resp = self.session.head(url, headers=req_headers, allow_redirects=True, timeout=(5, 10))
            if resp.status_code >= 400:
                resp = self.session.get(url, headers=req_headers, stream=True, allow_redirects=True, timeout=(5, 10))
            
            content_length = int(resp.headers.get("Content-Length", 0))
            accept_ranges = resp.headers.get("Accept-Ranges", "").lower() == "bytes"
            return content_length, accept_ranges
        except Exception:
            return 0, False

    def _download_part(
        self,
        url: str,
        start: int,
        end: int,
        part_file: str,
        progress_callback=None,
        stop_event: Optional[threading.Event] = None,
        headers: Optional[dict] = None,
        direct_write: bool = False,
        session: Optional[requests.Session] = None,
    ) -> int:
        req_headers = {
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
        }
        if headers:
            req_headers.update(headers)

        s = session or self.session
        resp = s.get(url, headers=req_headers, stream=True, timeout=(8, 25))
        try:
            if resp.status_code == 200 and start > 0:
                raise Non206RangeResponseError("Server returned 200 OK instead of 206 Partial Content")
            resp.raise_for_status()

            bytes_written = 0
            open_mode = "r+b" if direct_write else "wb"
            with open(part_file, open_mode) as f:
                if direct_write:
                    f.seek(start)
                # 64 KB buffer for fast packet delivery and responsive UI speed updates
                for chunk in resp.iter_content(chunk_size=65536):
                    if stop_event and stop_event.is_set():
                        return bytes_written
                    if chunk:
                        f.write(chunk)
                        bytes_written += len(chunk)
                        if progress_callback:
                            progress_callback(len(chunk))
            return bytes_written
        finally:
            try:
                resp.close()
            except Exception:
                pass

    def download(
        self,
        url: str,
        output_path: str,
        num_parts: int = 4,
        progress_callback: Optional[Callable[[int], None]] = None,
        stop_event: Optional[threading.Event] = None,
        headers: Optional[dict] = None,
        known_size: Optional[int] = None,
    ) -> DownloadResult:
        if stop_event and stop_event.is_set():
            return DownloadResult(
                success=False,
                bytes_downloaded=0,
                num_parts=num_parts,
                output_path=output_path,
                error="Download stopped by user",
            )

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if known_size and known_size > 0:
            total_size = known_size
            range_supported = True
        else:
            total_size, range_supported = self.probe(url, headers=headers)

        if stop_event and stop_event.is_set():
            return DownloadResult(
                success=False,
                bytes_downloaded=0,
                num_parts=num_parts,
                output_path=output_path,
                error="Download stopped by user",
            )

        active_session = self._create_session()

        try:
            # Segment sizing: allow requested parts while protecting tiny payload (<1KB)
            if total_size > 0:
                if total_size < 1000:
                    effective_parts = 1
                elif total_size < 5 * 1024 * 1024:
                    effective_parts = min(num_parts, 8)
                else:
                    effective_parts = num_parts
            else:
                effective_parts = num_parts

            def _do_single_stream() -> DownloadResult:
                try:
                    stream_headers = {"Accept-Encoding": "identity"}
                    if headers:
                        stream_headers.update(headers)
                    resp = active_session.get(url, headers=stream_headers, stream=True, timeout=(8, 30))
                    try:
                        resp.raise_for_status()
                        downloaded = 0
                        with open(output_path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=65536):
                                if stop_event and stop_event.is_set():
                                    return DownloadResult(
                                        success=False,
                                        bytes_downloaded=0,
                                        num_parts=1,
                                        output_path=output_path,
                                        error="Download stopped by user",
                                    )
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if progress_callback:
                                        progress_callback(len(chunk))
                        return DownloadResult(
                            success=True,
                            bytes_downloaded=downloaded,
                            num_parts=1,
                            output_path=output_path,
                        )
                    finally:
                        try:
                            resp.close()
                        except Exception:
                            pass
                except Exception as ex:
                    if os.path.exists(output_path):
                        try:
                            os.remove(output_path)
                        except Exception:
                            pass
                    return DownloadResult(
                        success=False,
                        bytes_downloaded=0,
                        num_parts=1,
                        output_path=output_path,
                        error=str(ex),
                    )

            if not range_supported or total_size <= 0 or effective_parts <= 1:
                return _do_single_stream()

            # Helper to execute multi-part download with given parts
            def _attempt_multi_part(parts_count: int) -> tuple[bool, Optional[str]]:
                part_size = total_size // parts_count
                ranges = []
                for i in range(parts_count):
                    start = i * part_size
                    end = total_size - 1 if i == parts_count - 1 else (i + 1) * part_size - 1
                    ranges.append((start, end))

                # IDM Multi-Part temporary directory next to output file (Instant start, ZERO disk pre-allocation freeze)
                temp_parts_dir = output_path + f".idm_parts_{parts_count}"
                os.makedirs(temp_parts_dir, exist_ok=True)
                part_files = [os.path.join(temp_parts_dir, f"part_{i}.tmp") for i in range(parts_count)]

                executor = ThreadPoolExecutor(max_workers=parts_count)
                try:
                    futures = []
                    batch_size = 8
                    # Ramp up in batches of 8 (matching IDM signature dynamic ramping)
                    for batch_start in range(0, parts_count, batch_size):
                        if stop_event and stop_event.is_set():
                            break
                        batch_ranges = ranges[batch_start : batch_start + batch_size]
                        for idx, r in enumerate(batch_ranges, start=batch_start):
                            f = executor.submit(
                                self._download_part,
                                url,
                                r[0],
                                r[1],
                                part_files[idx],
                                progress_callback,
                                stop_event,
                                headers,
                                False,
                                active_session,
                            )
                            futures.append(f)
                        if batch_start + batch_size < parts_count:
                            time.sleep(0.3)

                    for future in as_completed(futures):
                        future.result()

                    if stop_event and stop_event.is_set():
                        executor.shutdown(wait=False, cancel_futures=True)
                        shutil.rmtree(temp_parts_dir, ignore_errors=True)
                        return False, "Download stopped by user"

                    executor.shutdown(wait=True)

                    # High-speed sequential merge of completed parts into destination
                    with open(output_path, "wb") as outfile:
                        for p in part_files:
                            with open(p, "rb") as infile:
                                while True:
                                    buf = infile.read(16 * 1024 * 1024)
                                    if not buf:
                                        break
                                    outfile.write(buf)

                    shutil.rmtree(temp_parts_dir, ignore_errors=True)
                    return True, None
                except Exception as e:
                    executor.shutdown(wait=False, cancel_futures=True)
                    shutil.rmtree(temp_parts_dir, ignore_errors=True)
                    return False, str(e)

            # Attempt 1: Try with requested parts (e.g. 32 or 8)
            ok, err = _attempt_multi_part(effective_parts)
            if ok:
                return DownloadResult(
                    success=True,
                    bytes_downloaded=os.path.getsize(output_path),
                    num_parts=effective_parts,
                    output_path=output_path,
                )

            if stop_event and stop_event.is_set():
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
                return DownloadResult(
                    success=False,
                    bytes_downloaded=0,
                    num_parts=effective_parts,
                    output_path=output_path,
                    error="Download stopped by user",
                )

            # Attempt 2: If requested > 8 and server throttled / failed, dynamically drop to 8 parts
            if effective_parts > 8:
                if progress_callback:
                    progress_callback(-1)
                ok8, err8 = _attempt_multi_part(8)
                if ok8:
                    return DownloadResult(
                        success=True,
                        bytes_downloaded=os.path.getsize(output_path),
                        num_parts=8,
                        output_path=output_path,
                    )

            # Attempt 3: If server rejects parallel ranges (429/503/Cloudflare/etc.), gracefully fallback to single stream
            if progress_callback:
                progress_callback(-1)
            return _do_single_stream()
        finally:
            try:
                active_session.close()
            except Exception:
                pass
