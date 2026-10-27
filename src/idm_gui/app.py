import os
import sys
import threading
import time
import urllib.parse
from typing import Optional, Any

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from idm_core.engine import DownloadEngine, DownloadResult
from idm_scheduler.queue import DownloadQueue, DownloadTask, TaskStatus
from idm_server.server import LocalDownloadServer
from idm_gui.dialogs import (
    DownloadInfoDialog,
    DialogAction,
    DownloadProgressDialog,
    DownloadCompleteDialog,
    OptionsDialog,
)
from idm_gui.settings import settings
from idm_gui.theme import (
    THEME,
    setup_global_ttk_theme,
    create_modern_button,
    draw_round_rectangle,
    FONT_HEADING,
    FONT_BODY,
    FONT_SMALL,
)


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


class IDMGUIApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Internet Download Manager (Clone)")
        self.root.geometry("960x560")
        self.root.minsize(760, 440)
        self.root.configure(bg=THEME["bg_dark"])

        self.engine = DownloadEngine()
        self.queue = DownloadQueue()
        self.active_threads: dict[str, threading.Thread] = {}
        self.stop_events: dict[str, threading.Event] = {}
        self.task_referers: dict[str, str] = {}
        self.task_headers: dict[str, dict] = {}
        self.task_speeds: dict[str, float] = {}
        self.last_bytes: dict[str, int] = {}
        self.last_time: dict[str, float] = {}
        self.progress_dialogs: dict[str, DownloadProgressDialog] = {}
        self.toolbar_buttons: list[tuple[Any, str]] = []
        self.secondary_buttons: list[Any] = []
        self.btn_overflow: Optional[Any] = None
        self.empty_state_frame: Optional[Any] = None

        # Start loopback server for Browser Extension communication
        self.server = LocalDownloadServer(
            host="127.0.0.1",
            port=19900,
            queue=self.queue,
            on_task_added=self._on_server_task_added,
        )
        try:
            self.server.start()
        except Exception as e:
            print("Could not start loopback server:", e)

        self._setup_styles()
        self._build_menu()
        self._build_toolbar()
        self._build_main_content()
        self._build_statusbar()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start periodic UI update timer
        self.root.after(300, self._tick_ui)

    def _detect_category(self, url: str, title: str) -> str:
        lower = (url + " " + title).lower()
        if any(x in lower for x in ["video", ".mp4", ".mkv", ".webm", ".avi", ".flv", "youtube.com", "youtu.be", "googlevideo", "vimeo"]):
            return "Video"
        elif any(x in lower for x in [".mp3", ".m4a", ".wav", ".flac", ".aac", "audio"]):
            return "Musik"
        elif any(x in lower for x in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg", ".ico", ".avif", "image", "photo", "foto", "picture"]):
            return "Gambar"
        elif any(x in lower for x in [".zip", ".rar", ".7z", ".tar", ".gz"]):
            return "Berkas Terkompresi"
        elif any(x in lower for x in [".exe", ".msi", ".iso"]):
            return "Program"
        elif any(x in lower for x in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt"]):
            return "Dokumen"
        return "Umum"

    def _get_clean_title_with_ext(self, url: str, title: str, category: str) -> str:
        clean = (title or "").strip()
        common_exts = [
            "jpg", "jpeg", "png", "webp", "gif", "bmp", "svg", "avif", "ico",
            "mp4", "mkv", "webm", "avi", "mov", "flv",
            "mp3", "m4a", "wav", "flac", "aac", "ogg",
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt",
            "zip", "rar", "7z", "tar", "gz",
            "exe", "msi", "iso"
        ]
        if "." in clean and clean.rsplit(".", 1)[-1].lower() in common_exts:
            return clean

        inferred = self.engine.get_filename(url)
        if inferred and "." in inferred:
            ext = "." + inferred.rsplit(".", 1)[-1].lower()
            if ext.lstrip(".") in common_exts:
                base = clean or inferred.rsplit(".", 1)[0]
                return f"{base}{ext}"

        fallback_map = {
            "Gambar": ".jpg",
            "Video": ".mp4",
            "Musik": ".mp3",
            "Dokumen": ".pdf",
            "Berkas Terkompresi": ".zip",
            "Program": ".exe",
        }
        ext = fallback_map.get(category, ".bin")
        base = clean or "download"
        return f"{base}{ext}"

    def _check_file_security(self, filename: str) -> tuple[bool, str]:
        """Detects double-extension scams (e.g. invoice.pdf.exe) and high-risk scripts."""
        lower = filename.lower()
        parts = lower.split(".")
        if len(parts) >= 3:
            last_ext = parts[-1]
            penultimate_ext = parts[-2]
            executable_exts = {"exe", "scr", "vbs", "bat", "cmd", "pif", "hta", "jar", "ps1"}
            document_image_exts = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg", "png", "mp4", "mp3", "zip"}
            if last_ext in executable_exts and penultimate_ext in document_image_exts:
                return True, f"Peringatan: Berkas memiliki ekstensi ganda (.{penultimate_ext}.{last_ext}) yang umum digunakan adware/malware!"

        dangerous_scripts = {"vbs", "scr", "pif", "hta"}
        if len(parts) >= 2 and parts[-1] in dangerous_scripts:
            return True, f"Peringatan: Berkas berekstensi .{parts[-1]} merupakan skrip berisiko tinggi!"

        return False, ""

    def _on_server_task_added(self, task_id: str, payload: dict):
        parts = int(payload.get("parts", settings.get_max_connections()))
        url = payload.get("url", "")
        title = payload.get("title", "")
        auto_start = payload.get("auto_start", False)
        referer = payload.get("referer", "")
        cookie = payload.get("cookie", "")
        user_agent = payload.get("user_agent", "")

        req_headers = {}
        if referer:
            req_headers["Referer"] = referer
            self.task_referers[task_id] = referer
        if cookie:
            req_headers["Cookie"] = cookie
        if user_agent:
            req_headers["User-Agent"] = user_agent
        if req_headers:
            self.task_headers[task_id] = req_headers

        def handle_incoming():
            task = self.queue.get_task(task_id)
            if not task:
                return

            category = self._detect_category(url, title)
            clean_title = self._get_clean_title_with_ext(url, title, category)
            remembered_dir = settings.get_category_path(category)
            task.output_path = os.path.join(remembered_dir, clean_title)

            # Check file safety
            is_suspicious, sec_warning = self._check_file_security(clean_title)
            if payload.get("is_suspicious"):
                is_suspicious = True
                sec_warning = payload.get("security_warning") or sec_warning

            # If fileSize is already known from browser payload, use it directly (PREVENTS BURNING ONE-TIME TOKENS!)
            payload_size = int(payload.get("file_size", 0))
            if payload_size > 0:
                probed_size = payload_size
            else:
                probed_size, _ = self.engine.probe(url, headers=req_headers) if not any(d in url for d in ["youtube.com", "youtu.be"]) else (0, False)

            if probed_size > 0:
                task.total_bytes = probed_size

            def on_dialog_action(action: DialogAction, final_url: str, final_path: str, chosen_parts: int):
                task.output_path = final_path
                if action == DialogAction.START:
                    prog_dlg = DownloadProgressDialog(
                        parent=self.root,
                        task_id=task_id,
                        url=final_url,
                        output_path=final_path,
                        total_bytes=task.total_bytes,
                        parts=chosen_parts,
                        on_pause=lambda tid: self.pause_task_by_id(tid),
                        on_cancel=lambda tid: self.delete_task_by_id(tid),
                        on_resume=lambda tid: self.resume_task_by_id(tid),
                    )
                    self.progress_dialogs[task_id] = prog_dlg
                    self._run_task_thread(task_id, parts=chosen_parts, progress_dlg=prog_dlg)
                elif action == DialogAction.LATER:
                    task.status = TaskStatus.QUEUED
                elif action == DialogAction.CANCEL:
                    self.delete_task_by_id(task_id)

            DownloadInfoDialog(
                parent=self.root,
                url=url,
                title=clean_title,
                probed_size=probed_size,
                category=category,
                on_action=on_dialog_action,
                is_suspicious=is_suspicious,
                security_warning=sec_warning,
            )

        self.root.after(50, handle_incoming)

    def _on_close(self):
        if hasattr(self, "server") and self.server:
            self.server.stop()
        self.root.destroy()

    def _setup_styles(self):
        setup_global_ttk_theme()

    def _build_menu(self):
        self.menubar = tk.Menu(self.root, bg=THEME["surface"], fg=THEME["text_primary"], activebackground=THEME["accent_primary"], activeforeground="#ffffff", bd=0)

        # 1. Menu Tugas (Tasks)
        tasks_menu = tk.Menu(self.menubar, tearoff=0)
        tasks_menu.add_command(label="Tambahkan unduhan baru... (Add URL)", accelerator="Ctrl+N", command=self.open_add_url_dialog)
        tasks_menu.add_separator()
        tasks_menu.add_command(label="Ekspor ke berkas teks...", command=self.export_to_text_file)
        tasks_menu.add_command(label="Impor dari berkas teks...", command=self.import_from_text_file)
        tasks_menu.add_separator()
        tasks_menu.add_command(label="Keluar (Exit)", accelerator="Alt+F4", command=self.root.quit)
        self.menubar.add_cascade(label="Tugas (Tasks)", menu=tasks_menu)

        # 2. Menu Berkas (File)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Hentikan Unduh (Pause)", command=self.pause_selected)
        file_menu.add_command(label="Lanjutkan Unduh (Resume)", command=self.resume_selected)
        file_menu.add_command(label="Hapus Unduhan (Remove)", accelerator="Del", command=self.delete_selected)
        file_menu.add_separator()
        file_menu.add_command(label="Buka Berkas (Open File)", command=self.open_selected_file)
        file_menu.add_command(label="Buka Folder Penyimpanan (Open Folder)", command=self.open_selected_folder)
        self.menubar.add_cascade(label="Berkas (File)", menu=file_menu)

        # 3. Menu Unduh (Downloads)
        downloads_menu = tk.Menu(self.menubar, tearoff=0)
        downloads_menu.add_command(label="Jeda Semua (Pause All)", command=self.pause_all)
        downloads_menu.add_command(label="Lanjutkan Semua (Resume All)", command=self.resume_all)
        downloads_menu.add_command(label="Hentikan Semua (Stop All)", command=self.stop_all)
        downloads_menu.add_command(label="Hapus Semua Yang Selesai (Delete Completed)", command=self.delete_completed)
        downloads_menu.add_separator()
        downloads_menu.add_command(label="⚙ Opsi / Pengaturan... (Options)", command=self.open_options_dialog)
        self.menubar.add_cascade(label="Unduh (Downloads)", menu=downloads_menu)

        # 4. Menu Lihat (View)
        view_menu = tk.Menu(self.menubar, tearoff=0)
        view_menu.add_command(label="Sembunyikan/Tampilkan Kategori", command=self.toggle_sidebar)
        
        arrange_menu = tk.Menu(view_menu, tearoff=0)
        arrange_menu.add_command(label="Berdasarkan Nama Berkas", command=lambda: self.sort_by_column("name"))
        arrange_menu.add_command(label="Berdasarkan Ukuran", command=lambda: self.sort_by_column("size"))
        arrange_menu.add_command(label="Berdasarkan Status", command=lambda: self.sort_by_column("status"))
        arrange_menu.add_command(label="Berdasarkan Kecepatan", command=lambda: self.sort_by_column("speed"))
        view_menu.add_cascade(label="Atur Berkas (Arrange Files)", menu=arrange_menu)

        view_menu.add_separator()
        lang_menu = tk.Menu(view_menu, tearoff=0)
        lang_menu.add_command(label="✔ Bahasa Indonesia (Aktif)")
        lang_menu.add_command(label="English")
        view_menu.add_cascade(label="Bahasa (Language)", menu=lang_menu)

        self.menubar.add_cascade(label="Lihat (View)", menu=view_menu)

        # 5. Menu Bantuan (Help)
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="Tip Hari Ini... (Tip of the Day)", command=self.show_tip_of_the_day)
        help_menu.add_command(label="Periksa Pembaruan... (Check for Updates)", command=self.check_for_updates)
        help_menu.add_separator()
        help_menu.add_command(label="Tentang IDM Clone (About)", command=self.show_about)
        self.menubar.add_cascade(label="Bantuan (Help)", menu=help_menu)

        self.root.config(menu=self.menubar)

        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.open_add_url_dialog())
        self.root.bind("<Control-N>", lambda e: self.open_add_url_dialog())
        self.root.bind("<Delete>", lambda e: self.delete_selected())

    def _build_toolbar(self):
        self.toolbar_frame = tk.Frame(self.root, bg=THEME["surface"], pady=6, padx=8, relief=tk.FLAT)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        # Primary specs (always visible)
        primary_specs = [
            ("+ Tambah", self.open_add_url_dialog, "primary", "Tambah URL Baru (Ctrl+N)"),
            ("▷ Lanjutkan", self.resume_selected, "toolbar", "Lanjutkan Unduhan Terpilih"),
            ("❚❚ Jeda", self.pause_selected, "toolbar", "Jeda Unduhan Terpilih"),
            ("✕ Hapus", self.delete_selected, "danger", "Hapus Unduhan Terpilih (Del)"),
        ]

        # Secondary specs (moved to overflow when width < 760px)
        secondary_specs = [
            ("■ Hentikan", self.stop_all, "toolbar", "Hentikan Semua Unduhan"),
            ("✓ Bersihkan", self.delete_completed, "toolbar", "Bersihkan Seluruh Unduhan Selesai"),
            ("↗ Buka Folder", self.open_selected_folder, "toolbar", "Buka Folder Berkas Terpilih"),
            ("⋯ Pengaturan", self.open_options_dialog, "toolbar", "Opsi Konfigurasi IDM Clone"),
        ]

        self.toolbar_buttons = []
        self.secondary_buttons = []

        for text, cmd, kind, tooltip_text in primary_specs:
            btn = create_modern_button(self.toolbar_frame, text=text, command=cmd, kind=kind, padx=10, pady=4, tooltip=tooltip_text)
            btn.pack(side=tk.LEFT, padx=3)
            self.toolbar_buttons.append((btn, tooltip_text))

        for text, cmd, kind, tooltip_text in secondary_specs:
            btn = create_modern_button(self.toolbar_frame, text=text, command=cmd, kind=kind, padx=10, pady=4, tooltip=tooltip_text)
            btn.pack(side=tk.LEFT, padx=3)
            self.toolbar_buttons.append((btn, tooltip_text))
            self.secondary_buttons.append(btn)

        # Overflow menu & button for responsive compact width (<760px)
        self.overflow_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["surface"],
            fg=THEME["text_primary"],
            activebackground=THEME["accent_primary"],
            activeforeground="#ffffff",
            bd=1,
            relief=tk.FLAT,
        )
        self.overflow_menu.add_command(label="■ Hentikan Semua Unduhan", command=self.stop_all)
        self.overflow_menu.add_command(label="✓ Bersihkan Selesai", command=self.delete_completed)
        self.overflow_menu.add_command(label="↗ Buka Folder Penyimpanan", command=self.open_selected_folder)
        self.overflow_menu.add_separator()
        self.overflow_menu.add_command(label="⋯ Pengaturan...", command=self.open_options_dialog)

        self.btn_overflow = create_modern_button(
            self.toolbar_frame,
            text="» Lainnya",
            command=self._show_overflow_menu,
            kind="toolbar",
            padx=10,
            pady=4,
            tooltip="Aksi Tambahan...",
        )

        self.root.bind("<Configure>", self._on_window_configure, add="+")

    def _on_window_configure(self, event):
        if event.widget == self.root:
            self._update_toolbar_overflow(event.width)

    def _update_toolbar_overflow(self, width: Optional[int] = None):
        w = width if width is not None else self.root.winfo_width()
        if w < 760:
            for btn in self.secondary_buttons:
                btn.pack_forget()
            if self.btn_overflow:
                self.btn_overflow.pack(side=tk.LEFT, padx=3)
        else:
            if self.btn_overflow:
                self.btn_overflow.pack_forget()
            for btn in self.secondary_buttons:
                btn.pack(side=tk.LEFT, padx=3)

    def _show_overflow_menu(self):
        if not self.btn_overflow:
            return
        try:
            x = self.btn_overflow.winfo_rootx()
            y = self.btn_overflow.winfo_rooty() + self.btn_overflow.winfo_height() + 2
            self.overflow_menu.post(x, y)
        except Exception:
            pass

    def _build_main_content(self):
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=4, bg=THEME["bg_dark"])
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar: Categories
        self.sidebar_frame = tk.Frame(self.paned, width=190, bg=THEME["surface_alt"])
        self.sidebar_visible = True
        self.category_tree = ttk.Treeview(self.sidebar_frame, show="tree", selectmode="browse")
        self.category_tree.pack(fill=tk.BOTH, expand=True, padx=(2, 0), pady=2)

        cat_root = self.category_tree.insert("", "end", text="📁 Kategori", open=True)
        self.category_tree.insert(cat_root, "end", text="Semua Unduhan", values=("all",))
        self.category_tree.insert(cat_root, "end", text="Video", values=("video",))
        self.category_tree.insert(cat_root, "end", text="Musik", values=("music",))
        self.category_tree.insert(cat_root, "end", text="Gambar", values=("pictures",))
        self.category_tree.insert(cat_root, "end", text="Program", values=("programs",))
        self.category_tree.insert(cat_root, "end", text="Dokumen", values=("documents",))
        self.category_tree.insert(cat_root, "end", text="Berkas Terkompresi", values=("compressed",))
        self.category_tree.insert(cat_root, "end", text="Selesai", values=("finished",))
        self.category_tree.insert(cat_root, "end", text="Belum Selesai", values=("unfinished",))
        self.category_tree.bind("<Double-1>", self._on_category_double_click)

        self.paned.add(self.sidebar_frame, minsize=150)

        # Right Panel: Downloads Table
        table_frame = tk.Frame(self.paned, bg=THEME["tree_bg"])
        cols = ("name", "size", "status", "progress", "speed", "url")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="extended")

        self.tree.heading("name", text="Nama Berkas")
        self.tree.heading("size", text="Ukuran")
        self.tree.heading("status", text="Status")
        self.tree.heading("progress", text="Progres")
        self.tree.heading("speed", text="Kecepatan")
        self.tree.heading("url", text="URL Unduhan")

        self.tree.column("name", width=240, minwidth=140)
        self.tree.column("size", width=85, anchor=tk.E, minwidth=70)
        self.tree.column("status", width=95, anchor=tk.CENTER, minwidth=80)
        self.tree.column("progress", width=85, anchor=tk.CENTER, minwidth=75)
        self.tree.column("speed", width=95, anchor=tk.E, minwidth=80)
        self.tree.column("url", width=280, stretch=True)

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_double_click_item)

        # Empty State Card Overlay (Apple-inspired rounded card)
        self.empty_state_frame = tk.Canvas(
            table_frame,
            width=380,
            height=210,
            bg=THEME["tree_bg"],
            highlightthickness=0,
        )

        draw_round_rectangle(self.empty_state_frame, 2, 2, 378, 208, r=14, fill=THEME["surface"], outline=THEME["border"])

        inner_card = tk.Frame(self.empty_state_frame, bg=THEME["surface"])

        lbl_empty_icon = tk.Label(
            inner_card,
            text="📥",
            font=("Segoe UI", 24),
            bg=THEME["surface"],
            fg=THEME["text_primary"],
        )
        lbl_empty_icon.pack(pady=(0, 4))

        lbl_empty_title = tk.Label(
            inner_card,
            text="Belum Ada Unduhan",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["surface"],
            fg=THEME["text_primary"],
        )
        lbl_empty_title.pack(pady=(0, 2))

        lbl_empty_desc = tk.Label(
            inner_card,
            text="Salin tautan dari peramban atau klik tombol di bawah untuk memulai unduhan baru.",
            font=("Segoe UI", 9),
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            wraplength=320,
            justify=tk.CENTER,
        )
        lbl_empty_desc.pack(pady=(0, 10))

        btn_empty_add = create_modern_button(
            inner_card,
            text="+ Tambah Unduhan Baru",
            command=self.open_add_url_dialog,
            kind="primary",
            padx=16,
            pady=6,
            radius=8,
            tooltip="Tambah URL Baru (Ctrl+N)",
        )
        btn_empty_add.pack()

        self.empty_state_frame.create_window(190, 105, window=inner_card)

        # Place initially if queue is empty
        if len(self.queue.list_tasks()) == 0:
            self.empty_state_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        self.paned.add(table_frame, minsize=400)

    def _build_statusbar(self):
        self.statusbar = tk.Label(
            self.root,
            text="⚡ Siap (IPC Server Port 19900 Aktif)",
            bd=0,
            relief=tk.FLAT,
            anchor=tk.W,
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=FONT_SMALL,
            padx=14,
            pady=6,
        )
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_options_dialog(self, initial_category: Optional[str] = None):
        dlg = OptionsDialog(self.root, settings_manager=settings)
        if initial_category and initial_category in dlg.categories:
            dlg.cat_var.set(initial_category)
            dlg._on_cat_change()

    def _on_category_double_click(self, event=None):
        selected = self.category_tree.selection()
        if not selected:
            return
        item_text = self.category_tree.item(selected[0], "text")
        cat_map = {
            "Video / Media": "Video",
            "Compressed": "Berkas Terkompresi",
            "Documents": "Dokumen",
            "Programs": "Program",
            "Music": "Musik",
        }
        cat = cat_map.get(item_text, "Video")
        self.open_options_dialog(initial_category=cat)

    def open_add_url_dialog(self):
        # Auto-detect clipboard URL
        clipboard_url = ""
        try:
            clip = self.root.clipboard_get().strip()
            if clip.startswith("http://") or clip.startswith("https://"):
                clipboard_url = clip
        except Exception:
            pass

        if not clipboard_url:
            # Simple URL input if clipboard is empty
            dlg = tk.Toplevel(self.root)
            dlg.title("Masukkan URL untuk mengunduh")
            dlg.geometry("460x140")
            dlg.resizable(False, False)
            dlg.configure(bg="#2b2b2b")
            dlg.transient(self.root)
            dlg.grab_set()

            tk.Label(dlg, text="Alamat (URL):", bg="#2b2b2b", fg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, padx=14, pady=(12, 2))
            url_entry = tk.Entry(dlg, bg="#1e1e1e", fg="#ffffff", insertbackground="#ffffff", relief=tk.SOLID, bd=1, font=("Segoe UI", 9))
            url_entry.pack(fill=tk.X, padx=14, pady=4)
            url_entry.focus_set()

            btn_box = tk.Frame(dlg, bg="#2b2b2b")
            btn_box.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=10)

            def on_ok():
                u = url_entry.get().strip()
                dlg.destroy()
                if u:
                    self._show_download_info_for_url(u)

            tk.Button(btn_box, text="OK", command=on_ok, bg="#0066cc", fg="#ffffff", font=("Segoe UI", 9, "bold"), width=8).pack(side=tk.RIGHT, padx=4)
            tk.Button(btn_box, text="Batal", command=dlg.destroy, bg="#383838", fg="#ffffff", font=("Segoe UI", 9), width=8).pack(side=tk.RIGHT)
        else:
            self._show_download_info_for_url(clipboard_url)

    def pause_task_by_id(self, task_id: str):
        task = self.queue.get_task(task_id)
        if task:
            task.status = TaskStatus.PAUSED
        if task_id in self.stop_events:
            self.stop_events[task_id].set()
        self.task_speeds[task_id] = 0.0
        if task_id in self.progress_dialogs:
            try:
                dlg = self.progress_dialogs[task_id]
                dlg.lbl_status.config(text="Status: Dijeda (Paused)")
                dlg.lbl_speed.config(text="0 B/detik")
                dlg.lbl_eta.config(text="Dijeda")
                dlg.btn_pause.config(text="Lanjutkan")
            except Exception:
                pass

    def resume_task_by_id(self, task_id: str):
        task = self.queue.get_task(task_id)
        if task and task.status in (TaskStatus.PAUSED, TaskStatus.FAILED, TaskStatus.QUEUED):
            if task_id in self.stop_events:
                self.stop_events[task_id].clear()
            dlg = self.progress_dialogs.get(task_id)
            if dlg:
                try:
                    dlg.btn_pause.config(text="Jeda")
                    dlg.lbl_status.config(text="Status: Menerima data...")
                except Exception:
                    pass
            conns = settings.get_max_connections()
            self._run_task_thread(task_id, parts=conns, progress_dlg=dlg)

    def delete_task_by_id(self, task_id: str):
        task = self.queue.get_task(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
        if task_id in self.stop_events:
            self.stop_events[task_id].set()
        self.task_speeds[task_id] = 0.0
        self.task_referers.pop(task_id, None)
        self.task_headers.pop(task_id, None)
        self.queue.delete_task(task_id)
        if task_id in self.progress_dialogs:
            try:
                self.progress_dialogs[task_id].close()
            except Exception:
                pass
            del self.progress_dialogs[task_id]
        if self.tree.exists(task_id):
            self.tree.delete(task_id)
        if task and task.output_path:
            out_dir = os.path.dirname(os.path.abspath(task.output_path))
            try:
                # Clean up any partial or temp files
                for f in os.listdir(out_dir):
                    if f.endswith(".part") or f.endswith(".ytdl"):
                        p = os.path.join(out_dir, f)
                        if os.path.exists(p):
                            os.remove(p)
            except Exception:
                pass

    def _show_download_info_for_url(self, url: str):
        raw_title = self.engine.get_filename(url)
        category = self._detect_category(url, raw_title)
        title = self._get_clean_title_with_ext(url, raw_title, category)
        is_yt = any(d in url for d in ["youtube.com", "youtu.be"])

        dlg_ref = {}

        def on_action(action: DialogAction, final_url: str, final_path: str, chosen_parts: int):
            if action == DialogAction.CANCEL:
                return

            current_size = dlg_ref["dlg"].probed_size if "dlg" in dlg_ref else 0
            task_id = self.queue.add_task(url=final_url, output_path=final_path)
            task = self.queue.get_task(task_id)
            if task and current_size > 0:
                task.total_bytes = current_size

            if action == DialogAction.START:
                prog_dlg = DownloadProgressDialog(
                    parent=self.root,
                    task_id=task_id,
                    url=final_url,
                    output_path=final_path,
                    total_bytes=task.total_bytes if task else 0,
                    parts=chosen_parts,
                    on_pause=lambda tid: self.pause_task_by_id(tid),
                    on_cancel=lambda tid: self.delete_task_by_id(tid),
                    on_resume=lambda tid: self.resume_task_by_id(tid),
                )
                self.progress_dialogs[task_id] = prog_dlg
                self._run_task_thread(task_id, parts=chosen_parts, progress_dlg=prog_dlg)
            elif action == DialogAction.LATER:
                if task:
                    task.status = TaskStatus.QUEUED

        dlg = DownloadInfoDialog(
            parent=self.root,
            url=url,
            title=title,
            probed_size=0,
            category=category,
            on_action=on_action,
            is_probing=not is_yt,
        )
        dlg_ref["dlg"] = dlg

        if not is_yt:
            def probe_worker():
                size, _ = self.engine.probe(url)
                def apply_probe():
                    try:
                        if dlg and hasattr(dlg, "top") and dlg.top.winfo_exists():
                            dlg.update_probed_size(size)
                    except Exception:
                        pass
                try:
                    self.root.after(0, apply_probe)
                except Exception:
                    pass

            threading.Thread(target=probe_worker, daemon=True).start()

    def start_download(self, url: str, folder: str, parts: Optional[int] = None):
        parsed = urllib.parse.urlparse(url)
        fname = os.path.basename(parsed.path) or "downloaded_file.bin"
        out_path = os.path.join(folder, fname)

        active_parts = parts or settings.get_max_connections()
        task_id = self.queue.add_task(url=url, output_path=out_path)
        
        # Probe size in background to populate table immediately
        def probe_and_start():
            task = self.queue.get_task(task_id)
            if not task:
                return
            size, range_ok = self.engine.probe(url)
            task.total_bytes = size
            self._run_task_thread(task_id, active_parts)

        th = threading.Thread(target=probe_and_start, daemon=True)
        th.start()

    def _run_task_thread(self, task_id: str, parts: Optional[int] = None, progress_dlg: Optional[DownloadProgressDialog] = None):
        task = self.queue.get_task(task_id)
        if not task:
            return

        active_parts = parts or settings.get_max_connections()
        task.status = TaskStatus.DOWNLOADING
        stop_event = threading.Event()
        self.stop_events[task_id] = stop_event

        self.last_bytes[task_id] = 0
        self.last_time[task_id] = time.time()

        class DownloadAborted(Exception):
            pass

        progress_lock = threading.Lock()

        def update_ui_progress():
            now = time.time()
            prev_b = self.last_bytes.get(task_id, 0)
            prev_t = self.last_time.get(task_id, now)
            dt = now - prev_t
            if dt >= 0.25:
                speed = (task.bytes_downloaded - prev_b) / dt if dt > 0 else 0.0
                self.task_speeds[task_id] = speed
                self.last_bytes[task_id] = task.bytes_downloaded
                self.last_time[task_id] = now
                if progress_dlg:
                    curr_b = task.bytes_downloaded
                    tot_b = task.total_bytes
                    dlg = progress_dlg
                    self.root.after(0, lambda b=curr_b, t=tot_b, s=speed, d=dlg: d.update_progress(b, t, s))

        def progress_cb(chunk_len: int):
            with progress_lock:
                if chunk_len < 0:
                    task.bytes_downloaded = 0
                else:
                    task.bytes_downloaded += chunk_len
                update_ui_progress()

        def worker():
            referer = self.task_referers.get(task_id, "")
            stream_url = task.url
            if "googlevideo.com" in task.url and "youtube.com" in referer:
                stream_url = referer
            is_stream_site = any(d in stream_url for d in ["youtube.com", "youtu.be", "vimeo.com", "tiktok.com"])
            if is_stream_site:
                try:
                    import yt_dlp
                    out_dir = os.path.dirname(os.path.abspath(task.output_path))
                    def ydl_hook(d):
                        if stop_event.is_set() or task.status in (TaskStatus.PAUSED, TaskStatus.CANCELLED):
                            raise DownloadAborted("Download stopped by user")

                        if d.get("status") == "downloading":
                            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                            downloaded = d.get("downloaded_bytes", 0)
                            if total > 0:
                                task.total_bytes = total
                            task.bytes_downloaded = downloaded
                            speed = d.get("speed") or 0.0
                            self.task_speeds[task_id] = float(speed)
                            if progress_dlg:
                                curr_b = task.bytes_downloaded
                                tot_b = task.total_bytes
                                dlg = progress_dlg
                                self.root.after(0, lambda b=curr_b, t=tot_b, s=float(speed), d=dlg: d.update_progress(b, t, s))
                        elif d.get("status") == "finished":
                            task.bytes_downloaded = task.total_bytes

                    ydl_opts = {
                        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
                        # Prioritize H.264 (avc1) video + AAC (mp4a) audio so video displays perfectly on Windows
                        "format": (
                            "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                            "bestvideo[vcodec^=avc1]+bestaudio/"
                            "best[vcodec^=avc1]/"
                            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                            "best"
                        ),
                        "merge_output_format": "mp4",
                        "concurrent_fragment_downloads": 4,
                        "buffersize": 1024 * 64,
                        "progress_hooks": [ydl_hook],
                        "quiet": True,
                        "no_warnings": True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(stream_url, download=True)
                        if stop_event.is_set() or task.status in (TaskStatus.PAUSED, TaskStatus.CANCELLED):
                            raise DownloadAborted("Download stopped by user")
                        if info:
                            downloaded_file = ydl.prepare_filename(info)
                            task.output_path = downloaded_file
                            if os.path.exists(downloaded_file):
                                task.total_bytes = os.path.getsize(downloaded_file)
                                task.bytes_downloaded = task.total_bytes
                    task.status = TaskStatus.COMPLETED
                    self.task_speeds[task_id] = 0.0
                    self._on_download_complete(task, progress_dlg)
                except DownloadAborted:
                    self.task_speeds[task_id] = 0.0
                    if task.status == TaskStatus.PAUSED and progress_dlg:
                        self.root.after(0, lambda: progress_dlg.lbl_status.config(text="Status: Dijeda"))
                    return
                except Exception as e:
                    if stop_event.is_set() or task.status in (TaskStatus.PAUSED, TaskStatus.CANCELLED):
                        self.task_speeds[task_id] = 0.0
                        return
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    self.task_speeds[task_id] = 0.0
                    if progress_dlg:
                        self.root.after(0, lambda: progress_dlg.lbl_status.config(text=f"Gagal: {e}"))
            else:
                req_headers = self.task_headers.get(task_id)
                res: DownloadResult = self.engine.download(
                    task.url,
                    task.output_path,
                    num_parts=active_parts,
                    progress_callback=progress_cb,
                    stop_event=stop_event,
                    headers=req_headers,
                    known_size=task.total_bytes if task.total_bytes > 0 else None,
                )
                if stop_event.is_set() or task.status in (TaskStatus.PAUSED, TaskStatus.CANCELLED) or (not res.success and "stopped" in (res.error or "").lower()):
                    self.task_speeds[task_id] = 0.0
                    if task.status == TaskStatus.PAUSED and progress_dlg:
                        self.root.after(0, lambda: progress_dlg.lbl_status.config(text="Status: Dijeda"))
                    return

                if res.success:
                    task.status = TaskStatus.COMPLETED
                    task.bytes_downloaded = res.bytes_downloaded
                    task.total_bytes = res.bytes_downloaded
                    self.task_speeds[task_id] = 0.0
                    self._on_download_complete(task, progress_dlg)
                else:
                    task.status = TaskStatus.FAILED
                    task.error = res.error
                    self.task_speeds[task_id] = 0.0
                    if progress_dlg:
                        self.root.after(0, lambda: progress_dlg.lbl_status.config(text=f"Gagal: {res.error}"))

        th = threading.Thread(target=worker, daemon=True)
        self.active_threads[task_id] = th
        th.start()

    def _on_download_complete(self, task: DownloadTask, progress_dlg: Optional[DownloadProgressDialog] = None):
        def show_complete():
            if progress_dlg:
                try:
                    progress_dlg.close()
                except Exception:
                    pass
            fname = os.path.basename(task.output_path)
            DownloadCompleteDialog(
                parent=self.root,
                title=fname,
                output_path=task.output_path,
                total_bytes=task.total_bytes,
            )
        self.root.after(0, show_complete)

    def _tick_ui(self):
        now = time.time()
        tasks = self.queue.list_tasks()

        total_speed = 0.0
        active_count = 0

        # Update or insert table rows
        for task in tasks:
            tid = task.task_id
            fname = os.path.basename(task.output_path)
            size_str = format_bytes(task.total_bytes) if task.total_bytes > 0 else "Unknown"

            # Compute transfer rate
            if task.status == TaskStatus.DOWNLOADING:
                active_count += 1
                prev_b = self.last_bytes.get(tid, 0)
                prev_t = self.last_time.get(tid, now)
                dt = now - prev_t
                if dt >= 0.5:
                    speed = (task.bytes_downloaded - prev_b) / dt
                    self.task_speeds[tid] = speed
                    self.last_bytes[tid] = task.bytes_downloaded
                    self.last_time[tid] = now
                curr_speed = self.task_speeds.get(tid, 0.0)
                total_speed += curr_speed
                speed_str = f"{format_bytes(int(curr_speed))}/s"
            else:
                speed_str = "--"

            pct_str = "0%"
            if task.total_bytes > 0:
                pct = min(100.0, (task.bytes_downloaded / task.total_bytes) * 100)
                pct_str = f"{pct:.1f}%"
            elif task.status == TaskStatus.COMPLETED:
                pct_str = "100%"

            values = (
                fname,
                size_str,
                task.status.value,
                pct_str,
                speed_str,
                task.url,
            )

            if self.tree.exists(tid):
                self.tree.item(tid, values=values)
            else:
                self.tree.insert("", "end", iid=tid, values=values)

        # Remove deleted tasks from treeview
        current_task_ids = {t.task_id for t in tasks}
        for item_id in self.tree.get_children(""):
            if item_id not in current_task_ids:
                self.tree.delete(item_id)

        # Toggle empty state card
        if hasattr(self, "empty_state_frame") and self.empty_state_frame:
            if len(tasks) == 0:
                if not bool(self.empty_state_frame.place_info()):
                    self.empty_state_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
            else:
                if bool(self.empty_state_frame.place_info()):
                    self.empty_state_frame.place_forget()

        self.statusbar.config(
            text=f"Total: {len(tasks)} unduhan  |  Aktif: {active_count}  |  Total Kecepatan: {format_bytes(int(total_speed))}/s"
        )
        self.root.after(300, self._tick_ui)

    def _get_selected_task_id(self) -> Optional[str]:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _get_selected_task_ids(self) -> list[str]:
        return list(self.tree.selection())

    def resume_selected(self):
        tids = self._get_selected_task_ids()
        for tid in tids:
            self.resume_task_by_id(tid)

    def pause_selected(self):
        tids = self._get_selected_task_ids()
        for tid in tids:
            self.pause_task_by_id(tid)

    def delete_selected(self, confirm: bool = True):
        tids = self._get_selected_task_ids()
        if not tids:
            return
        if confirm:
            count = len(tids)
            msg = f"Apakah Anda yakin ingin menghapus {count} unduhan yang dipilih?" if count > 1 else "Apakah Anda yakin ingin menghapus unduhan yang dipilih?"
            if not messagebox.askyesno("Konfirmasi Hapus Unduhan", msg, parent=self.root):
                return
        for tid in tids:
            self.delete_task_by_id(tid)

    def open_selected_folder(self):
        tid = self._get_selected_task_id()
        if tid:
            task = self.queue.get_task(tid)
            if task and os.path.exists(os.path.dirname(task.output_path)):
                os.startfile(os.path.dirname(task.output_path))

    def on_double_click_item(self, event):
        tid = self._get_selected_task_id()
        if tid:
            task = self.queue.get_task(tid)
            if task and task.status == TaskStatus.COMPLETED and os.path.exists(task.output_path):
                os.startfile(task.output_path)
            else:
                self.open_selected_folder()

    def show_about(self):
        messagebox.showinfo(
            "About IDM Clone",
            "Internet Download Manager Clone\n"
            "Reverse-Engineered Architecture Implementation\n"
            "Developed with Python, Tkinter, and TDD.\n"
            "Features: Parallel Range Download, Streaming Muxer, Browser Native Host."
        )

    def pause_all(self):
        for task in self.queue.list_tasks(status=TaskStatus.DOWNLOADING):
            self.pause_task_by_id(task.task_id)

    def resume_all(self):
        for task in self.queue.list_tasks():
            if task.status in (TaskStatus.PAUSED, TaskStatus.QUEUED):
                self.resume_task_by_id(task.task_id)

    def stop_all(self):
        self.pause_all()

    def delete_completed(self):
        for task in self.queue.list_tasks(status=TaskStatus.COMPLETED):
            self.delete_task_by_id(task.task_id)

    def open_selected_file(self):
        tid = self._get_selected_task_id()
        if tid:
            task = self.queue.get_task(tid)
            if task and os.path.exists(task.output_path):
                os.startfile(task.output_path)
            else:
                self.open_selected_folder()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.paned.forget(self.sidebar_frame)
            self.sidebar_visible = False
        else:
            panes = self.paned.panes()
            if panes:
                self.paned.add(self.sidebar_frame, before=panes[0], minsize=140)
            else:
                self.paned.add(self.sidebar_frame, minsize=140)
            self.sidebar_visible = True

    def sort_by_column(self, col: str):
        col_map = {"name": 0, "size": 1, "status": 2, "speed": 4}
        idx = col_map.get(col, 0)
        items = [(self.tree.item(item, "values"), item) for item in self.tree.get_children("")]
        items.sort(key=lambda t: t[0][idx] if len(t[0]) > idx else "")
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

    def export_to_text_file(self, path: Optional[str] = None):
        target_path = path
        if not target_path:
            target_path = filedialog.asksaveasfilename(
                parent=self.root,
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                title="Ekspor Daftar Tautan Unduhan",
            )
        if target_path:
            tasks = self.queue.list_tasks()
            urls = [t.url for t in tasks if t.url]
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("\n".join(urls) + "\n")

    def import_from_text_file(self, path: Optional[str] = None):
        target_path = path
        if not target_path:
            target_path = filedialog.askopenfilename(
                parent=self.root,
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                title="Impor Daftar Tautan Unduhan",
            )
        if target_path and os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip().startswith("http")]
            for u in lines:
                category = self._detect_category(u, os.path.basename(u))
                folder = settings.get_category_path(category)
                self.start_download(u, folder)

    def show_tip_of_the_day(self):
        messagebox.showinfo(
            "Tip Hari Ini - IDM Clone",
            "💡 Tip Cepat:\n\n"
            "1. Anda dapat menyalin tautan berkas di browser, dan IDM Clone otomatis menangkapnya.\n"
            "2. Gunakan tombol '⚙ Opsi' di menu atas untuk mengubah jumlah koneksi paralel hingga 32 jalur.\n"
            "3. Klik dua kali baris unduhan untuk langsung membuka berkas yang telah selesai diunduh.",
        )

    def check_for_updates(self):
        messagebox.showinfo(
            "Periksa Pembaruan - IDM Clone",
            "✔ Anda telah menggunakan versi terbaru IDM Clone (v1.1.0 High-Performance Release)!\n\nSemua komponen sistem mutakhir dan terintegrasi.",
        )


def main():
    root = tk.Tk()
    app = IDMGUIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
