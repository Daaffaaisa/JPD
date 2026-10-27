from enum import Enum
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional

from idm_gui.settings import settings
from idm_gui.theme import (
    THEME,
    FONT_TITLE,
    FONT_HEADING,
    FONT_BODY,
    FONT_SMALL,
    create_modern_button,
    apply_theme_to_toplevel,
)


class DialogAction(str, Enum):
    START = "START"
    LATER = "LATER"
    CANCEL = "CANCEL"


def format_size_id(num_bytes: int) -> str:
    """Formats bytes in Indonesian style (e.g. 337,84 MB)."""
    if num_bytes <= 0:
        return "Tidak diketahui"
    elif num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        val = num_bytes / 1024
        return f"{val:.2f} KB".replace(".", ",")
    elif num_bytes < 1024 * 1024 * 1024:
        val = num_bytes / (1024 * 1024)
        return f"{val:.2f} MB".replace(".", ",")
    else:
        val = num_bytes / (1024 * 1024 * 1024)
        return f"{val:.2f} GB".replace(".", ",")


def format_time_left(seconds: float) -> str:
    """Formats remaining time in Indonesian style (e.g. 13 menit 58 detik)."""
    if seconds <= 0:
        return "Selesai"
    s = int(seconds)
    if s < 60:
        return f"{s} detik"
    elif s < 3600:
        m = s // 60
        rem_s = s % 60
        return f"{m} menit {rem_s} detik" if rem_s > 0 else f"{m} menit"
    else:
        h = s // 3600
        rem_m = (s % 3600) // 60
        return f"{h} jam {rem_m} menit" if rem_m > 0 else f"{h} jam"


class DownloadInfoDialog:
    """Replicates the classic IDM 'Informasi Berkas Unduhan' (Download File Info) dialog."""

    CATEGORIES = {
        "Video": "Video",
        "Musik": "Music",
        "Program": "Programs",
        "Dokumen": "Documents",
        "Berkas Terkompresi": "Compressed",
        "Umum": "General",
    }

    def __init__(
        self,
        parent: tk.Tk,
        url: str,
        title: str = "",
        probed_size: int = 0,
        category: str = "Video",
        default_folder: Optional[str] = None,
        on_action: Optional[Callable[[DialogAction, str, str, int], None]] = None,
        is_suspicious: bool = False,
        security_warning: Optional[str] = None,
        is_probing: bool = False,
    ):
        self.parent = parent
        self.url = url
        self.title = title or "download.bin"
        self.probed_size = probed_size
        self.category = category
        self.action = DialogAction.CANCEL
        self.on_action = on_action
        self.is_suspicious = is_suspicious
        self.security_warning = security_warning
        self.is_probing = is_probing

        downloads_dir = default_folder or os.path.join(os.path.expanduser("~"), "Downloads")
        self.cat_folder = settings.get_category_path(self.category, default_base=downloads_dir)
        self.output_path = os.path.join(self.cat_folder, self.title)

        self._build_ui()

    def _build_ui(self):
        self.top = tk.Toplevel(self.parent)
        self.top.title("Info Unduh Berkas")
        self.top.geometry("540x340")
        self.top.resizable(False, False)
        self.top.configure(bg="#2b2b2b")
        self.top.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.top.bind("<Escape>", lambda e: self._on_cancel())
        try:
            self.top.grab_set()
        except Exception:
            pass

        # Center dialog directly on the monitor screen
        self.top.update_idletasks()
        try:
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            x = max(0, (screen_w - 540) // 2)
            y = max(0, (screen_h - 330) // 2)
            self.top.geometry(f"540x330+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.attributes("-topmost", True)
            self.top.after(500, lambda: self.top.attributes("-topmost", False))
            self.top.focus_force()
        except Exception:
            pass

        # Dark theme styling colors
        BG_COLOR = "#2b2b2b"
        FG_COLOR = "#ffffff"
        ENTRY_BG = "#1e1e1e"
        BORDER_COLOR = "#4a4a4a"

        if self.is_suspicious and self.security_warning:
            self.lbl_security_warning = tk.Label(
                self.top,
                text=f"⚠ {self.security_warning}",
                bg="#990000",
                fg="#ffffff",
                font=("Segoe UI", 8, "bold"),
                padx=10,
                pady=4,
                wraplength=500,
                justify=tk.LEFT,
            )
            self.lbl_security_warning.pack(fill=tk.X, side=tk.TOP)
        else:
            self.lbl_security_warning = None

        main_frame = tk.Frame(self.top, bg=BG_COLOR, padx=16, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. URL Row
        tk.Label(main_frame, text="URL:", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=3
        )
        self.url_var = tk.StringVar(master=self.top, value=self.url)
        url_entry = tk.Entry(
            main_frame,
            textvariable=self.url_var,
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 9),
        )
        url_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=(6, 0), pady=3)

        # 2. Kategori Row
        tk.Label(main_frame, text="Kategori:", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky=tk.W, pady=3
        )
        cat_frame = tk.Frame(main_frame, bg=BG_COLOR)
        cat_frame.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=(6, 0), pady=3)

        self.cat_var = tk.StringVar(master=self.top, value=self.category)
        self.cat_cb = ttk.Combobox(
            cat_frame,
            textvariable=self.cat_var,
            values=list(self.CATEGORIES.keys()),
            state="readonly",
            font=("Segoe UI", 9),
            width=22,
        )
        self.cat_cb.pack(side=tk.LEFT)
        self.cat_cb.bind("<<ComboboxSelected>>", self._on_cat_change)

        self.btn_add_cat = tk.Button(
            cat_frame,
            text="+",
            command=self._on_add_category,
            bg="#3a3a3a",
            fg=FG_COLOR,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 8, "bold"),
            width=2,
            padx=2,
        )
        self.btn_add_cat.pack(side=tk.LEFT, padx=(4, 0))

        # 3. Simpan Sebagai Row
        tk.Label(main_frame, text="Simpan Sebagai:", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=3
        )
        save_frame = tk.Frame(main_frame, bg=BG_COLOR)
        save_frame.grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=(6, 0), pady=3)

        self.path_var = tk.StringVar(master=self.top, value=self.output_path)

        def _on_path_var_trace(*args):
            try:
                p = self.path_var.get().strip()
                if p:
                    abs_p = os.path.abspath(p)
                    d = abs_p if os.path.isdir(abs_p) else os.path.dirname(abs_p)
                    if hasattr(self, "lbl_sub_folder") and self.lbl_sub_folder:
                        self.lbl_sub_folder.config(text=d)
            except Exception:
                pass

        self.path_var.trace_add("write", _on_path_var_trace)

        path_entry = tk.Entry(
            save_frame,
            textvariable=self.path_var,
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 9),
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_browse = tk.Button(
            save_frame,
            text="...",
            command=self._on_browse,
            bg="#3a3a3a",
            fg=FG_COLOR,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 8, "bold"),
            width=3,
        )
        btn_browse.pack(side=tk.RIGHT, padx=(4, 0))

        # 4. Checkbox Ingat Jalur (Default unchecked so single-file destination changes don't overwrite category default)
        self.remember_var = tk.BooleanVar(master=self.top, value=False)
        self.cb_remember = tk.Checkbutton(
            main_frame,
            text=f'Ingat jalur ini untuk kategori "{self.category}"',
            variable=self.remember_var,
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor="#1e1e1e",
            activebackground=BG_COLOR,
            activeforeground=FG_COLOR,
            font=("Segoe UI", 8),
        )
        self.cb_remember.grid(row=3, column=1, sticky=tk.W, padx=(6, 0), pady=(0, 2))

        # Sub-container displaying the category folder path (matching IDM screenshot)
        self.lbl_sub_folder = tk.Label(
            main_frame,
            text=self.cat_folder,
            bg="#202020",
            fg="#cccccc",
            relief=tk.SOLID,
            bd=1,
            anchor=tk.W,
            padx=8,
            pady=3,
            font=("Segoe UI", 8),
        )
        self.lbl_sub_folder.grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=(6, 0), pady=(0, 4))

        # 5. File Info Frame (Icon, Size, Description)
        info_frame = tk.Frame(main_frame, bg="#232323", relief=tk.SOLID, bd=1, padx=10, pady=8)
        info_frame.grid(row=5, column=0, columnspan=3, sticky=tk.NSEW, pady=(4, 8))

        # Left: Icon & Size
        icon_box = tk.Frame(info_frame, bg="#232323")
        icon_box.pack(side=tk.LEFT, padx=(0, 16))

        # Native Windows registered default application icon for file extension (VLC, WinRAR, etc.)
        self.icon_label = tk.Label(icon_box, bg="#232323")
        self.icon_label.pack()
        self._tk_icon = None
        self._update_app_icon(self.title)

        size_text = "Memeriksa ukuran..." if (self.is_probing and self.probed_size <= 0) else format_size_id(self.probed_size)
        self.lbl_size = tk.Label(icon_box, text=size_text, bg="#232323", fg="#ffffff", font=("Segoe UI", 9, "bold"))
        self.lbl_size.pack(pady=(2, 0))

        # Right: Description box
        desc_box = tk.Frame(info_frame, bg="#232323")
        desc_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(desc_box, text="Deskripsi:", bg="#232323", fg="#aaaaaa", font=("Segoe UI", 8)).pack(anchor=tk.W)
        self.desc_entry = tk.Entry(
            desc_box,
            bg="#181818",
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 9),
        )
        self.desc_entry.pack(fill=tk.X, expand=True, pady=(2, 0))

        # Parallel Connections indicator
        active_conns = settings.get_max_connections()
        self.conn_label = tk.Label(
            desc_box,
            text=f"⚡ Akselerasi: {active_conns} Koneksi Paralel HTTP Range",
            bg="#232323",
            fg="#28a745",
            font=("Segoe UI", 8, "italic"),
        )
        self.conn_label.pack(anchor=tk.W, pady=(4, 0))

        # 6. Action Buttons Row (Unduh Nanti, Mulai Unduh, Batal)
        btn_frame = tk.Frame(main_frame, bg=BG_COLOR)
        btn_frame.grid(row=5, column=0, columnspan=3, sticky=tk.E, pady=(8, 0))

        btn_later = create_modern_button(btn_frame, "Unduh Nanti", self._on_later, kind="secondary", padx=12, pady=4)
        btn_later.pack(side=tk.LEFT, padx=4)

        btn_start = create_modern_button(btn_frame, "Mulai Unduh", self._on_start, kind="primary", padx=16, pady=4)
        btn_start.pack(side=tk.LEFT, padx=4)
        btn_start.focus_set()  # Default button (Enter key triggers Mulai Unduh)

        btn_cancel = create_modern_button(btn_frame, "Batal", self._on_cancel, kind="secondary", padx=12, pady=4)
        btn_cancel.pack(side=tk.LEFT, padx=4)

        self.top.bind("<Return>", lambda e: self._on_start())
        self.top.bind("<Escape>", lambda e: self._on_cancel())

        main_frame.columnconfigure(1, weight=1)

    def _update_app_icon(self, filename: str):
        try:
            from PIL import ImageTk
            from idm_gui.icon_utils import get_extension_icon_image
            icon_img = get_extension_icon_image(filename, size=36)
            self._tk_icon = ImageTk.PhotoImage(icon_img)
            if hasattr(self, "icon_label") and self.icon_label:
                self.icon_label.config(image=self._tk_icon)
        except Exception:
            pass

    def update_probed_size(self, size: int):
        self.probed_size = size
        self.is_probing = False
        try:
            if hasattr(self, "lbl_size") and self.lbl_size and self.lbl_size.winfo_exists():
                self.lbl_size.config(text=format_size_id(size))
        except Exception:
            pass

    def _on_add_category(self):
        try:
            from tkinter import simpledialog
            new_cat = simpledialog.askstring("Tambah Kategori Baru", "Masukkan nama kategori baru:", parent=self.top)
            if new_cat and new_cat.strip():
                new_cat = new_cat.strip()
                cur_vals = list(self.cat_cb["values"])
                if new_cat not in cur_vals:
                    cur_vals.append(new_cat)
                    self.cat_cb["values"] = cur_vals
                self.cat_var.set(new_cat)
                self._on_cat_change()
        except Exception:
            pass

    def _on_cat_change(self, event=None):
        cat = self.cat_var.get()
        self.category = cat
        cur_file = os.path.basename(self.path_var.get())
        self.cat_folder = settings.get_category_path(cat)
        new_path = os.path.join(self.cat_folder, cur_file)
        self.path_var.set(new_path)
        self._update_app_icon(cur_file)
        if hasattr(self, "cb_remember") and self.cb_remember:
            self.cb_remember.config(text=f'Ingat jalur ini untuk kategori "{cat}"')
        if hasattr(self, "lbl_sub_folder") and self.lbl_sub_folder:
            self.lbl_sub_folder.config(text=self.cat_folder)
        self.remember_var.set(False)

    def _on_browse(self):
        cur_path = self.path_var.get().strip()
        initial_dir = os.path.dirname(os.path.abspath(cur_path)) if cur_path else os.path.expanduser("~/Downloads")
        if not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~/Downloads")
        initial_file = (os.path.basename(cur_path) if cur_path else self.title) or "download.bin"

        # Temporarily release modal grab so Windows native folder picker is not blocked
        try:
            self.top.grab_release()
        except Exception:
            pass

        # Folder picker: select destination folder for category directly (like IDM [...])
        chosen_dir = filedialog.askdirectory(
            parent=self.top,
            initialdir=initial_dir,
            title="Pilih Folder Penyimpanan untuk Kategori",
        )

        # Restore modal grab and lift to foreground
        try:
            self.top.grab_set()
            self.top.lift()
            self.top.focus_force()
        except Exception:
            pass

        if chosen_dir:
            chosen_dir = os.path.abspath(chosen_dir)
            new_path = os.path.join(chosen_dir, initial_file)
            self.path_var.set(new_path)
            self.cat_folder = chosen_dir
            self._update_app_icon(initial_file)
            if hasattr(self, "lbl_sub_folder") and self.lbl_sub_folder:
                self.lbl_sub_folder.config(text=chosen_dir)

    def _on_start(self):
        self.action = DialogAction.START
        self._finish()

    def _on_later(self):
        self.action = DialogAction.LATER
        self._finish()

    def _on_cancel(self):
        self.action = DialogAction.CANCEL
        try:
            self.top.destroy()
        except Exception:
            pass
        if self.on_action:
            parts = settings.get_max_connections()
            self.on_action(self.action, self.url, self.path_var.get().strip(), parts)

    def _finish(self):
        final_path = self.path_var.get().strip()
        final_cat = self.cat_var.get()
        if final_path:
            abs_p = os.path.abspath(final_path)
            if os.path.isdir(abs_p):
                target_dir = abs_p
                final_path = os.path.join(abs_p, self.title or "download.bin")
            else:
                target_dir = os.path.dirname(abs_p)

            if self.remember_var.get():
                settings.set_category_path(final_cat, target_dir)

        self.top.destroy()
        if self.on_action:
            parts = settings.get_max_connections()
            self.on_action(self.action, self.url, final_path, parts)


class DownloadProgressDialog:
    """Replicates the active IDM download progress window (with tabs, ETA, speed, and thread segments)."""

    def __init__(
        self,
        parent: tk.Tk,
        task_id: str,
        url: str,
        output_path: str,
        total_bytes: int = 0,
        parts: int = 4,
        on_pause: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[str], None]] = None,
        on_resume: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self.task_id = task_id
        self.url = url
        self.output_path = output_path
        self.total_bytes = total_bytes
        self.parts = parts
        self.on_pause = on_pause
        self.on_cancel = on_cancel
        self.on_resume = on_resume

        self.filename = os.path.basename(output_path) or "download.bin"
        self.show_details = True
        self.start_time = time.time()

        self._build_ui()

    def _build_ui(self):
        self.top = tk.Toplevel(self.parent)
        self.top.title(f"0% {self.filename}")
        self.top.geometry("560x440")
        self.top.minsize(500, 360)
        self.top.configure(bg="#2b2b2b")
        self.top.protocol("WM_DELETE_WINDOW", self._on_cancel_click)

        # Center on screen and bring to front
        self.top.update_idletasks()
        try:
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            x = max(0, (screen_w - 560) // 2)
            y = max(0, (screen_h - 440) // 2)
            self.top.geometry(f"560x440+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.attributes("-topmost", True)
            self.top.after(500, lambda: self.top.attributes("-topmost", False))
            self.top.focus_force()
        except Exception:
            pass

        BG = "#2b2b2b"
        FG = "#ffffff"
        BOX_BG = "#222222"

        # Tab Header Row
        tab_frame = tk.Frame(self.top, bg="#1e1e1e", padx=6, pady=4)
        tab_frame.pack(fill=tk.X)

        self.lbl_tab1 = tk.Label(tab_frame, text="Status unduhan", bg=BG, fg=FG, font=("Segoe UI", 9, "bold"), padx=8, pady=3, relief=tk.SOLID, bd=1)
        self.lbl_tab1.pack(side=tk.LEFT, padx=2)
        self.lbl_tab2 = tk.Label(tab_frame, text="Pembatas Kecepatan (Segera Hadir)", bg="#1e1e1e", fg=THEME["text_disabled"], font=("Segoe UI", 8, "italic"), padx=6, pady=3, cursor="arrow")
        self.lbl_tab2.pack(side=tk.LEFT, padx=2)
        self.lbl_tab3 = tk.Label(tab_frame, text="Opsi saat selesai (Segera Hadir)", bg="#1e1e1e", fg=THEME["text_disabled"], font=("Segoe UI", 8, "italic"), padx=6, pady=3, cursor="arrow")
        self.lbl_tab3.pack(side=tk.LEFT, padx=2)

        content_frame = tk.Frame(self.top, bg=BG, padx=12, pady=8)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Info Box (bordered)
        info_box = tk.Frame(content_frame, bg=BOX_BG, relief=tk.SOLID, bd=1, padx=10, pady=8)
        info_box.pack(fill=tk.X, pady=(0, 8))

        def add_info_row(row, label_text, default_val):
            tk.Label(info_box, text=label_text, bg=BOX_BG, fg="#aaaaaa", font=("Segoe UI", 8), anchor=tk.W).grid(
                row=row, column=0, sticky=tk.W, pady=1
            )
            val_lbl = tk.Label(info_box, text=default_val, bg=BOX_BG, fg=FG, font=("Segoe UI", 8, "bold"), anchor=tk.W)
            val_lbl.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=1)
            return val_lbl

        disp_url = self.url if len(self.url) < 65 else self.url[:62] + "..."
        add_info_row(0, "URL Unduhan:", disp_url)
        self.lbl_status = add_info_row(1, "Status:", "Menerima data...")
        self.lbl_file_size = add_info_row(2, "Ukuran berkas:", format_size_id(self.total_bytes))
        self.lbl_downloaded = add_info_row(3, "Diunduh:", "0 B ( 0 % )")
        self.lbl_speed = add_info_row(4, "Tingkat transfer:", "0 B/detik")
        self.lbl_eta = add_info_row(5, "Waktu tersisa:", "Menghitung...")
        add_info_row(6, "Kemampuan resume:", "Ya")

        info_box.columnconfigure(1, weight=1)

        # Main Progress Bar
        bar_frame = tk.Frame(content_frame, bg=BG)
        bar_frame.pack(fill=tk.X, pady=(0, 6))

        self.progress_canvas = tk.Canvas(bar_frame, height=20, bg=THEME["progress_bg"], highlightthickness=1, highlightbackground=THEME["border"])
        self.progress_canvas.pack(fill=tk.X)
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill=THEME["progress_fill"], outline="")
        self.progress_text = self.progress_canvas.create_text(260, 10, text="0%", fill="#ffffff", font=("Segoe UI", 9, "bold"))

        # Action Buttons
        btn_row = tk.Frame(content_frame, bg=BG)
        btn_row.pack(fill=tk.X, pady=(0, 8))

        self.btn_toggle = create_modern_button(btn_row, "<< Sembunyikan detail", self._toggle_details, kind="secondary", padx=10, pady=3)
        self.btn_toggle.pack(side=tk.LEFT)

        self.btn_cancel = create_modern_button(btn_row, "Batal", self._on_cancel_click, kind="danger", padx=14, pady=3)
        self.btn_cancel.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_pause = create_modern_button(btn_row, "Jeda", self._on_pause_click, kind="secondary", padx=14, pady=3)
        self.btn_pause.pack(side=tk.RIGHT)

        # Detail Frame (Multi-segment visual bar + Connection table)
        self.detail_frame = tk.Frame(content_frame, bg=BG)
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            self.detail_frame,
            text="Progres posisi mulai dan unduh berdasarkan koneksi",
            bg=BG,
            fg="#aaaaaa",
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, pady=(0, 2))

        # Segment Multi-connection Visualizer Canvas
        self.seg_canvas = tk.Canvas(self.detail_frame, height=22, bg=THEME["progress_bg"], highlightthickness=1, highlightbackground=THEME["border"])
        self.seg_canvas.pack(fill=tk.X, pady=(0, 6))

        # Connections Treeview
        tree_frame = tk.Frame(self.detail_frame, bg=BG)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.conn_tree = ttk.Treeview(tree_frame, columns=("num", "dl", "info"), show="headings", height=4)
        self.conn_tree.heading("num", text="N.")
        self.conn_tree.heading("dl", text="Diunduh")
        self.conn_tree.heading("info", text="Info")

        self.conn_tree.column("num", width=45, anchor=tk.CENTER)
        self.conn_tree.column("dl", width=120, anchor=tk.E)
        self.conn_tree.column("info", width=220, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.conn_tree.yview)
        self.conn_tree.configure(yscrollcommand=tree_scroll.set)

        self.conn_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for i in range(1, self.parts + 1):
            self.conn_tree.insert("", "end", iid=str(i), values=(f"Koneksi {i}", "0 B", "Menerima data..."))

    def _toggle_details(self):
        if self.show_details:
            self.detail_frame.pack_forget()
            self.btn_toggle.config(text="Tampilkan detail >>")
            self.top.geometry("560x250")
            self.show_details = False
        else:
            self.detail_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_toggle.config(text="<< Sembunyikan detail")
            self.top.geometry("560x440")
            self.show_details = True

    def _on_pause_click(self):
        if self.btn_pause.cget("text") == "Lanjutkan":
            if hasattr(self, "on_resume") and self.on_resume:
                self.on_resume(self.task_id)
            self.btn_pause.config(text="Jeda")
            self.lbl_status.config(text="Menerima data...")
        else:
            if self.on_pause:
                self.on_pause(self.task_id)
            self.btn_pause.config(text="Lanjutkan")
            self.lbl_status.config(text="Dijeda")
            self.lbl_speed.config(text="0 B/detik")
            self.lbl_eta.config(text="Dijeda")

    def _on_cancel_click(self):
        if self.on_cancel:
            self.on_cancel(self.task_id)
        self.close()

    def update_progress(
        self,
        bytes_downloaded: int,
        total_bytes: int,
        speed_bps: float,
        part_progress: Optional[list[dict]] = None,
    ):
        try:
            if self.btn_pause.cget("text") == "Lanjutkan":
                # Currently paused, do not overwrite paused state
                return

            pct = 0.0
            if total_bytes > 0:
                pct = min(100.0, (bytes_downloaded / total_bytes) * 100)

            self.top.title(f"{int(pct)}% {self.filename}")

            self.lbl_file_size.config(text=format_size_id(total_bytes))
            self.lbl_downloaded.config(
                text=f"{format_size_id(bytes_downloaded)} ( {pct:.2f} % )".replace(".", ",")
            )
            self.lbl_speed.config(text=f"{format_size_id(int(speed_bps))}/detik")

            if speed_bps > 0 and total_bytes > bytes_downloaded:
                rem_sec = (total_bytes - bytes_downloaded) / speed_bps
                self.lbl_eta.config(text=format_time_left(rem_sec))
            elif pct >= 100.0:
                self.lbl_eta.config(text="Selesai")

            canvas_w = self.progress_canvas.winfo_width() or 520
            fill_w = int(canvas_w * (pct / 100.0))
            self.progress_canvas.coords(self.progress_rect, 0, 0, fill_w, 20)
            self.progress_canvas.coords(self.progress_text, canvas_w // 2, 10)
            self.progress_canvas.itemconfig(self.progress_text, text=f"{pct:.1f}%")

            seg_w = self.seg_canvas.winfo_width() or 520
            self.seg_canvas.delete("all")
            chunk_width = seg_w / max(1, self.parts)
            for i in range(self.parts):
                x0 = i * chunk_width
                part_pct = min(1.0, (pct / 100.0))
                self.seg_canvas.create_rectangle(x0, 2, x0 + (chunk_width * part_pct), 20, fill="#007acc", outline="")
                if i > 0:
                    self.seg_canvas.create_line(x0, 0, x0, 22, fill="#e74c3c", width=2)

            if part_progress:
                for p in part_progress:
                    iid = str(p.get("id"))
                    if self.conn_tree.exists(iid):
                        self.conn_tree.item(iid, values=(f"Koneksi {iid}", format_size_id(p.get("downloaded", 0)), p.get("status", "Menerima data...")))
            else:
                per_part = bytes_downloaded // max(1, self.parts)
                for i in range(1, self.parts + 1):
                    iid = str(i)
                    if self.conn_tree.exists(iid):
                        self.conn_tree.item(iid, values=(f"Koneksi {i}", format_size_id(per_part), "Menerima data..."))
        except Exception:
            pass

    def close(self):
        try:
            self.top.destroy()
        except Exception:
            pass


class DownloadCompleteDialog:
    """Pop-up modal shown when download finishes, offering Buka, Buka Folder, and Selesai."""

    def __init__(
        self,
        parent: tk.Tk,
        title: str,
        output_path: str,
        total_bytes: int = 0,
    ):
        self.parent = parent
        self.title = title
        self.output_path = output_path
        self.total_bytes = total_bytes

        self._build_ui()

    def _build_ui(self):
        self.top = tk.Toplevel(self.parent)
        self.top.title("Unduhan Selesai")
        self.top.geometry("480x210")
        self.top.resizable(False, False)
        self.top.configure(bg="#2b2b2b")

        self.top.update_idletasks()
        try:
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            x = max(0, (screen_w - 480) // 2)
            y = max(0, (screen_h - 210) // 2)
            self.top.geometry(f"480x210+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.attributes("-topmost", True)
            self.top.after(500, lambda: self.top.attributes("-topmost", False))
            self.top.focus_force()
        except Exception:
            pass

        BG = "#2b2b2b"
        FG = "#ffffff"

        content = tk.Frame(self.top, bg=BG, padx=16, pady=16)
        content.pack(fill=tk.BOTH, expand=True)

        hdr_frame = tk.Frame(content, bg=BG)
        hdr_frame.pack(fill=tk.X, pady=(0, 10))

        chk_canvas = tk.Canvas(hdr_frame, width=32, height=32, bg=BG, highlightthickness=0)
        chk_canvas.pack(side=tk.LEFT, padx=(0, 10))
        chk_canvas.create_oval(2, 2, 30, 30, fill="#28a745", outline="#1e7e34")
        chk_canvas.create_line(8, 16, 14, 22, 24, 10, fill="#ffffff", width=3)

        tk.Label(
            hdr_frame,
            text="Unduhan Telah Selesai!",
            bg=BG,
            fg="#28a745",
            font=("Segoe UI", 12, "bold"),
        ).pack(side=tk.LEFT, anchor=tk.CENTER)

        det_box = tk.Frame(content, bg="#222222", relief=tk.SOLID, bd=1, padx=10, pady=8)
        det_box.pack(fill=tk.X, pady=(0, 14))

        tk.Label(det_box, text=f"Berkas: {self.title}", bg="#222222", fg=FG, font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(fill=tk.X)
        tk.Label(det_box, text=f"Ukuran: {format_size_id(self.total_bytes)}", bg="#222222", fg="#aaaaaa", font=("Segoe UI", 8), anchor=tk.W).pack(fill=tk.X)
        tk.Label(det_box, text=f"Lokasi: {self.output_path}", bg="#222222", fg="#888888", font=("Segoe UI", 8), anchor=tk.W).pack(fill=tk.X)

        btn_box = tk.Frame(content, bg=BG)
        btn_box.pack(fill=tk.X)

        btn_open = create_modern_button(btn_box, "Buka", self._on_open, kind="primary", padx=14, pady=4)
        btn_open.pack(side=tk.RIGHT, padx=4)
        btn_open.focus_set()

        btn_folder = create_modern_button(btn_box, "Buka Folder", self._on_open_folder, kind="secondary", padx=12, pady=4)
        btn_folder.pack(side=tk.RIGHT, padx=4)

        btn_done = create_modern_button(btn_box, "Selesai", self.close, kind="secondary", padx=12, pady=4)
        btn_done.pack(side=tk.RIGHT, padx=4)

    def _on_open(self):
        try:
            if os.path.exists(self.output_path):
                os.startfile(self.output_path)
        except Exception:
            pass
        self.close()

    def _on_open_folder(self):
        try:
            folder = os.path.dirname(os.path.abspath(self.output_path))
            if os.path.exists(folder):
                os.startfile(folder)
        except Exception:
            pass
        self.close()

    def close(self):
        try:
            self.top.destroy()
        except Exception:
            pass


class OptionsDialog:
    """Dialog Opsi / Pengaturan IDM Clone multi-tab (Umum, Jenis Berkas, Simpan ke, Koneksi) ala IDM asli."""

    def __init__(self, parent: tk.Tk, settings_manager=None):
        self.parent = parent
        self.sm = settings_manager or settings
        self.categories = ["Video", "Musik", "Gambar", "Program", "Dokumen", "Berkas Terkompresi", "Umum"]
        self.conn_options = ["1", "2", "4", "8", "16", "24", "32"]
        self._build_ui()

    def _build_ui(self):
        self.top = tk.Toplevel(self.parent)
        self.top.title("Opsi Konfigurasi IDM Clone")
        self.top.geometry("560x430")
        self.top.resizable(False, False)
        self.top.configure(bg="#2b2b2b")
        try:
            self.top.grab_set()
        except Exception:
            pass

        # Center on screen
        self.top.update_idletasks()
        try:
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            x = max(0, (screen_w - 560) // 2)
            y = max(0, (screen_h - 430) // 2)
            self.top.geometry(f"560x430+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.focus_force()
        except Exception:
            pass

        BG = "#2b2b2b"
        FG = "#ffffff"
        ENTRY_BG = "#1e1e1e"

        main_frame = tk.Frame(self.top, bg=BG, padx=12, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Style the notebook
        style = ttk.Style()
        style.configure("Options.TNotebook", background=BG)
        style.configure("Options.TNotebook.Tab", padding=[10, 4], font=("Segoe UI", 9))

        self.notebook = ttk.Notebook(main_frame, style="Options.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # ---------------- TAB 1: UMUM (General) ----------------
        tab_general = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_general, text="Umum")

        tk.Label(
            tab_general,
            text="Integrasi Peramban Lanjutan (Browser Integration):",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        browser_integration = self.sm.data.get("browser_integration", {})
        self.cb_chrome_var = tk.BooleanVar(value=browser_integration.get("chrome", True))
        self.cb_edge_var = tk.BooleanVar(value=browser_integration.get("edge", True))
        self.cb_firefox_var = tk.BooleanVar(value=browser_integration.get("firefox", True))
        self.cb_opera_var = tk.BooleanVar(value=browser_integration.get("opera", False))

        browsers_frame = tk.Frame(tab_general, bg="#202020", relief=tk.SOLID, bd=1, padx=10, pady=8)
        browsers_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Checkbutton(browsers_frame, text="Google Chrome", variable=self.cb_chrome_var, bg="#202020", fg=FG, selectcolor=ENTRY_BG, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=1)
        tk.Checkbutton(browsers_frame, text="Microsoft Edge", variable=self.cb_edge_var, bg="#202020", fg=FG, selectcolor=ENTRY_BG, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=1)
        tk.Checkbutton(browsers_frame, text="Mozilla Firefox", variable=self.cb_firefox_var, bg="#202020", fg=FG, selectcolor=ENTRY_BG, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=1)
        tk.Checkbutton(browsers_frame, text="Opera Browser", variable=self.cb_opera_var, bg="#202020", fg=FG, selectcolor=ENTRY_BG, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=1)

        self.cb_startup_var = tk.BooleanVar(value=self.sm.data.get("autorun_startup", True))
        tk.Checkbutton(tab_general, text="Jalankan IDM Clone saat Windows dinyalakan", variable=self.cb_startup_var, bg=BG, fg=FG, selectcolor=ENTRY_BG, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=2)

        self.cb_clipboard_var = tk.BooleanVar(value=self.sm.data.get("monitor_clipboard", True))
        tk.Checkbutton(tab_general, text="Pantau clipboard untuk tautan unduhan otomatis", variable=self.cb_clipboard_var, bg=BG, fg=FG, selectcolor=ENTRY_BG, font=("Segoe UI", 9)).pack(anchor=tk.W, pady=2)

        tk.Label(tab_general, text="⚡ Port IPC Loopback: 127.0.0.1:19900 (Aktif & Siap)", bg=BG, fg="#28a745", font=("Segoe UI", 8, "italic")).pack(anchor=tk.W, pady=(8, 0))

        # ---------------- TAB 2: JENIS BERKAS (File Types) ----------------
        tab_types = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_types, text="Jenis Berkas")

        tk.Label(
            tab_types,
            text="Otomatis mulai unduh berkas dengan ekstensi berikut:",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        DEFAULT_EXTS = "3GP 7Z AAC ACE AIF ARJ ASF AVI BIN BZ2 EXE GZ GZIP IMG ISO LZH M4A M4V MKV MOV MP3 MP4 MPA MPE MPEG MPG MSI MSU OGG OGV PDF PLJ PPS PPT PPTX QT R0* R1* RA RAR RPM SEA SIT SITX TAR TIF TIFF TXT WAV WMA WMV Z ZIP"
        self.exts_var = tk.StringVar(value=self.sm.data.get("file_types", DEFAULT_EXTS))
        self.exts_entry = tk.Text(tab_types, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 9), height=5, wrap=tk.WORD)
        self.exts_entry.insert("1.0", self.exts_var.get())
        self.exts_entry.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            tab_types,
            text="Jangan mulai unduh otomatis dari situs berikut (Pengecualian):",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 4))

        self.exceptions_var = tk.StringVar(value=self.sm.data.get("exceptions", "*.speedtest.net *.fast.com"))
        self.exceptions_entry = tk.Entry(tab_types, textvariable=self.exceptions_var, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 9))
        self.exceptions_entry.pack(fill=tk.X, pady=(0, 4))
        tk.Label(tab_types, text="Ketik domain dipisahkan spasi (contoh: *.speedtest.net *.fast.com)", bg=BG, fg="#888888", font=("Segoe UI", 8)).pack(anchor=tk.W)

        # ---------------- TAB 3: SIMPAN KE (Save To) ----------------
        tab_save = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_save, text="Simpan ke")

        tk.Label(
            tab_save,
            text="Folder Penyimpanan per Kategori:",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 8))

        cat_frame = tk.Frame(tab_save, bg=BG)
        cat_frame.pack(fill=tk.X, pady=4)
        tk.Label(cat_frame, text="Pilih Kategori:", bg=BG, fg=FG, font=("Segoe UI", 9), width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.cat_var = tk.StringVar(value=self.categories[0])
        self.cat_combo = ttk.Combobox(cat_frame, textvariable=self.cat_var, values=self.categories, state="readonly", width=22)
        self.cat_combo.pack(side=tk.LEFT, padx=4)
        self.cat_combo.bind("<<ComboboxSelected>>", self._on_cat_change)

        path_frame = tk.Frame(tab_save, bg=BG)
        path_frame.pack(fill=tk.X, pady=(6, 14))
        tk.Label(path_frame, text="Folder Simpan:", bg=BG, fg=FG, font=("Segoe UI", 9), width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.sm.get_category_path(self.categories[0]))
        self.path_entry = tk.Entry(path_frame, textvariable=self.path_var, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 9))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 6))

        btn_browse = tk.Button(path_frame, text="...", command=self._on_browse, bg="#3a3a3a", fg=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 8, "bold"), width=3)
        btn_browse.pack(side=tk.RIGHT)

        # Temporary folder
        sep = tk.Frame(tab_save, bg="#444444", height=1)
        sep.pack(fill=tk.X, pady=(0, 10))

        tk.Label(tab_save, text="Direktori Berkas Sementara (Temporary Directory):", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 6))
        temp_frame = tk.Frame(tab_save, bg=BG)
        temp_frame.pack(fill=tk.X)
        self.temp_var = tk.StringVar(value=self.sm.data.get("temp_dir", os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")))
        self.temp_entry = tk.Entry(temp_frame, textvariable=self.temp_var, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 9))
        self.temp_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        btn_temp_browse = tk.Button(temp_frame, text="...", command=self._on_browse_temp, bg="#3a3a3a", fg=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 8, "bold"), width=3)
        btn_temp_browse.pack(side=tk.RIGHT)

        # ---------------- TAB 4: KONEKSI (Connection) ----------------
        tab_conn = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_conn, text="Koneksi")

        tk.Label(
            tab_conn,
            text="Tipe / Kecepatan Sambungan:",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        conn_type_combo = ttk.Combobox(
            tab_conn,
            values=["Kecepatan Tinggi: Sambungan Langsung (Ethernet/Kabel) / Wi-Fi / 4G", "Kecepatan Sedang: 3G / ADSL", "Kecepatan Rendah: Dial Up / VPN"],
            state="readonly",
        )
        conn_type_combo.current(0)
        conn_type_combo.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            tab_conn,
            text="Maks. Jumlah Koneksi (Parallel Connections):",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        conn_frame = tk.Frame(tab_conn, bg=BG)
        conn_frame.pack(fill=tk.X, pady=2)
        cur_conn = str(self.sm.get_max_connections())
        self.conn_var = tk.StringVar(value=cur_conn)
        self.conn_combo = ttk.Combobox(conn_frame, textvariable=self.conn_var, values=self.conn_options, state="readonly", width=8)
        self.conn_combo.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(conn_frame, text="jalur (32 = Kecepatan Maksimum IDM)", bg=BG, fg="#28a745", font=("Segoe UI", 8, "italic")).pack(side=tk.LEFT)

        tk.Label(
            tab_conn,
            text="* IDM Clone menggunakan akselerasi multi-koneksi paralel bertahap (kelipatan 8)",
            bg=BG,
            fg="#888888",
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, pady=(8, 0))

        # Bottom Action buttons
        btn_box = tk.Frame(main_frame, bg=BG)
        btn_box.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))

        btn_save = create_modern_button(btn_box, "Simpan", self._on_save, kind="primary", padx=16, pady=4)
        btn_save.pack(side=tk.RIGHT, padx=4)

        btn_cancel = create_modern_button(btn_box, "Batal", self.top.destroy, kind="secondary", padx=12, pady=4)
        btn_cancel.pack(side=tk.RIGHT, padx=4)

    def _on_cat_change(self, event=None):
        cat = self.cat_var.get()
        self.path_var.set(self.sm.get_category_path(cat))

    def _on_browse(self):
        try:
            self.top.grab_release()
        except Exception:
            pass

        initial_dir = self.path_var.get().strip() or os.path.expanduser("~/Downloads")
        chosen = filedialog.askdirectory(parent=self.top, initialdir=initial_dir, title="Pilih Folder untuk Kategori")

        try:
            self.top.grab_set()
            self.top.lift()
            self.top.focus_force()
        except Exception:
            pass

        if chosen:
            chosen = os.path.abspath(chosen)
            self.path_var.set(chosen)

    def _on_browse_temp(self):
        initial = self.temp_var.get().strip() or os.path.expanduser("~/AppData/Local/Temp")
        chosen = filedialog.askdirectory(parent=self.top, initialdir=initial, title="Pilih Folder Sementara")
        if chosen:
            self.temp_var.set(os.path.abspath(chosen))

    def _on_save(self):
        cat = self.cat_var.get()
        p = self.path_var.get().strip()
        if p:
            self.sm.set_category_path(cat, os.path.abspath(p))

        # Save connection limit
        try:
            val = int(self.conn_var.get())
            self.sm.set_max_connections(val)
        except Exception:
            pass

        # Save browser integration, autorun, file types and temp dir
        try:
            self.sm.data["browser_integration"] = {
                "chrome": bool(self.cb_chrome_var.get()),
                "edge": bool(self.cb_edge_var.get()),
                "firefox": bool(self.cb_firefox_var.get()),
                "opera": bool(self.cb_opera_var.get()),
            }
            self.sm.data["autorun_startup"] = bool(self.cb_startup_var.get())
            self.sm.data["monitor_clipboard"] = bool(self.cb_clipboard_var.get())
            self.sm.data["file_types"] = self.exts_entry.get("1.0", tk.END).strip()
            self.sm.data["exceptions"] = self.exceptions_var.get().strip()
            self.sm.data["temp_dir"] = self.temp_var.get().strip()
            self.sm._save()
        except Exception:
            pass

        self.top.destroy()
