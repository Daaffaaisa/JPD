# IDM Clone - Full Desktop App & Browser Extension

A high-performance download manager replicating the architecture of **Internet Download Manager (IDM)**, equipped with a **Desktop GUI**, **Browser Extension (Chrome/Edge/Firefox)**, and a **Multipart Range Acceleration Engine**, developed strictly with **Test-Driven Development (TDD)**.

---

## 🏛 Architecture Mapping (IDM Binaries -> IDM Clone Modules)

Based on the static inspection and binary disassembly of `C:\Program Files (x86)\Internet Download Manager`:

| IDM Shipped Binary / Component | IDM Clone Architecture Module | Responsibility & Features |
|---|---|---|
| `IDMan.exe` (Core Engine) | `idm_core.engine:DownloadEngine` | HTTP Range probing (`Accept-Ranges: bytes`), multi-part segmented downloading, parallel chunks via `ThreadPoolExecutor`, and byte reassembly. |
| `IDMVMPrs.dll` (Video Media Parser) | `idm_media.parser:StreamParser` | Streaming playlist & manifest parsing (HLS `.m3u8` playlists and MPEG-DASH `.mpd` XML). |
| `idmvconv.dll` (Media Muxer) | `idm_media.muxer:StreamMuxer` | Transmuxing, segment concatenation, and combining segmented media into continuous containers (`.ts`, `.mp4`). |
| `IDMMsgHost.exe` & `idmBroker.exe` | `idm_broker.broker:NativeMessageBroker` | Browser integration via WebExtension standard Native Messaging (length-prefixed JSON stdio protocol for Chrome, Edge, and Firefox). |
| IDM Scheduler (`scheduler.chm` & `idmindex.dll`) | `idm_scheduler.queue:DownloadQueue` | Thread-safe task scheduler, priority queue, pause/resume state machine (`QUEUED`, `DOWNLOADING`, `COMPLETED`, `PAUSED`, `FAILED`). |
| `IDMIntegrator64.exe` & manifests | `scripts/register_extension.py` & `manifests/` | Windows Registry integration for Native Messaging host registrations in Chrome, Edge, and Firefox. |
| User Interface & CLI | `idm_clone.cli:main` | Command-line interface with `download`, `stream`, `broker`, and queue control. |

---

## 🚀 Quick Start Guide

### 1. Jalankan Desktop GUI (Mirip IDM)
Cukup klik dua kali berkas:
```text
run_gui.bat
```
Atau via terminal:
```bash
uv run idm-gui
```
Fitur GUI:
- **Toolbar**: ➕ Add URL, ▶ Resume, ⏸ Pause, 🗑 Delete, 📁 Open Folder.
- **Tabel Unduhan**: Nama file, Ukuran, Status, Persentase Progress, Transfer Rate (Speed/s), dan URL.
- **Kategori**: All Downloads, Compressed, Documents, Programs, Video, Finished, Unfinished.
- **Add URL Dialog**: Input URL dengan clipboard auto-detection, browse lokasi simpan, dan pemilihan koneksi paralel (1-16 bagian).

### 2. Pasang Ekstensi Browser (Chrome / Edge / Firefox)
1. Daftarkan host ke Windows Registry dengan mengklik dua kali:
   ```text
   register_browser.bat
   ```
2. Buka `chrome://extensions/` atau `edge://extensions/`.
3. Aktifkan **Developer mode** di pojok kanan atas.
4. Klik **Load unpacked** dan pilih folder:
   ```text
   F:\Hermes Project\REA\idm_clone\extension
   ```
5. Ekstensi aktif dengan tombol melayang *"Download Video"* dan klik kanan *"Download with IDM Clone"*.

---

## 💻 CLI Usage

### 1. Multi-Part Segmented Download (Parallel HTTP Range Chunks)
```bash
uv run idm-clone download https://example.com/largefile.zip -o myfile.zip -p 8
```
- `-p, --parts`: Number of concurrent connections/threads (default: 4).
- Checks whether remote server supports HTTP Range; automatically falls back to single-stream if not supported.

### 2. Stream Media Download (HLS & MPEG-DASH)
```bash
uv run idm-clone stream https://example.com/live/playlist.m3u8 -o movie.ts
```
- Automatically parses all segments from `.m3u8` or `.mpd` manifests.
- Downloads segments concurrently and concatenates them using `StreamMuxer`.

### 3. Native Messaging Broker Mode (For Browser Extensions)
```bash
uv run idm-clone broker
```
- Runs in stdio mode listening for binary length-prefixed JSON packets from Chrome, Edge, or Firefox.

### 4. Register Browser Integration
```bash
uv run python scripts/register_extension.py
```
- Registers `com.idmclone.host` in Windows Registry (`HKCU\Software\Google\Chrome\NativeMessagingHosts`, `HKCU\Software\Microsoft\Edge\NativeMessagingHosts`, and `HKCU\Software\Mozilla\NativeMessagingHosts`).

---

## 🧪 Test-Driven Development (TDD) Verification

All seams were tested red-to-green:
- `tests/test_download_engine.py`: Unit tests for range probing, multipart chunks, and data integrity against mock HTTP server.
- `tests/test_stream_media.py`: Unit tests for HLS m3u8 and MPEG-DASH manifest parsing and segment concatenation.
- `tests/test_native_broker.py`: Unit tests for 32-bit length prefix encoding/decoding and IPC command dispatching.
- `tests/test_scheduler_queue.py`: Unit tests for priority queueing, task status tracking, and engine integration.
- `tests/test_integration.py`: End-to-end integration test verifying Browser Command -> Queue -> Engine -> Assembly.
- `tests/test_cli.py`: CLI parsing and command execution tests.
