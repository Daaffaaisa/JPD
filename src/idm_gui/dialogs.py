from enum import Enum
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional

from idm_gui.settings import settings
from idm_gui.i18n import (
    tr,
    get_current_lang,
    format_size_id,
    format_time_left,
    get_category_display_name,
    get_canonical_category_key,
    CATEGORY_KEYS,
)
from idm_gui.theme import (
    THEME,
    FONT_TITLE,
    FONT_HEADING,
    FONT_BODY,
    FONT_SMALL,
    create_modern_button,
    apply_theme_to_toplevel,
    setup_global_ttk_theme,
    apply_window_icon,
)


class DialogAction(str, Enum):
    START = "START"
    LATER = "LATER"
    CANCEL = "CANCEL"


class DownloadInfoDialog:
    """Replicates the classic IDM 'Informasi Berkas Unduhan' (Download File Info) dialog."""

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
        self.category = get_canonical_category_key(category)
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
        try:
            setup_global_ttk_theme()
        except Exception:
            pass
        self.top = tk.Toplevel(self.parent)
        apply_window_icon(self.top)
        self.top.title(tr("dlg_info_title"))
        self.top.geometry("580x300")
        self.top.minsize(540, 290)
        self.top.resizable(True, True)
        self.top.configure(bg=THEME["surface"])
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
            x = max(0, (screen_w - 580) // 2)
            y = max(0, (screen_h - 300) // 2)
            self.top.geometry(f"580x300+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.attributes("-topmost", True)
            self.top.after(500, lambda: self.top.attributes("-topmost", False))
            self.top.focus_force()
        except Exception:
            pass

        # Dark theme styling colors
        BG_COLOR = THEME["surface"]
        FG_COLOR = THEME["text_primary"]
        ENTRY_BG = THEME["input_bg"]
        CARD_BG = THEME["surface_alt"]
        BORDER_COLOR = THEME["border"]

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
        tk.Label(main_frame, text=tr("dlg_info_url"), bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 9, "bold")).grid(
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
        tk.Label(main_frame, text=tr("dlg_info_category"), bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky=tk.W, pady=3
        )
        cat_frame = tk.Frame(main_frame, bg=BG_COLOR)
        cat_frame.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=(6, 0), pady=3)

        display_categories = [get_category_display_name(k) for k in CATEGORY_KEYS]
        current_display = get_category_display_name(self.category)
        self.cat_var = tk.StringVar(master=self.top, value=current_display)
        self.cat_cb = ttk.Combobox(
            cat_frame,
            textvariable=self.cat_var,
            values=display_categories,
            state="readonly",
            font=("Segoe UI", 9),
            width=22,
        )
        self.cat_cb.pack(side=tk.LEFT)
        self.cat_cb.bind("<<ComboboxSelected>>", self._on_cat_change)

        self.btn_add_cat = create_modern_button(
            cat_frame,
            text="+",
            command=self._on_add_category,
            kind="secondary",
            padx=8,
            pady=2,
            radius=6,
            tooltip=tr("dlg_info_tip_add_cat"),
        )
        self.btn_add_cat.pack(side=tk.LEFT, padx=(4, 0))

        # 3. Simpan Sebagai Row
        tk.Label(main_frame, text=tr("dlg_info_save_as"), bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 9, "bold")).grid(
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

        self.btn_browse = create_modern_button(
            save_frame,
            text="...",
            command=self._on_browse,
            kind="secondary",
            padx=8,
            pady=2,
            radius=6,
            tooltip=tr("dlg_info_tip_browse"),
        )
        self.btn_browse.pack(side=tk.RIGHT, padx=(4, 0))

        # 4. Checkbox Ingat Jalur (Default unchecked so single-file destination changes don't overwrite category default)
        self.remember_var = tk.BooleanVar(master=self.top, value=False)
        self.cb_remember = tk.Checkbutton(
            main_frame,
            text=tr("dlg_info_remember", cat=current_display),
            variable=self.remember_var,
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=FG_COLOR,
            font=("Segoe UI", 8),
        )
        self.cb_remember.grid(row=3, column=1, sticky=tk.W, padx=(6, 0), pady=(0, 2))

        # Sub-container displaying the category folder path (matching IDM screenshot)
        self.lbl_sub_folder = tk.Label(
            main_frame,
            text=self.cat_folder,
            bg=CARD_BG,
            fg=THEME["text_secondary"],
            relief=tk.SOLID,
            bd=1,
            anchor=tk.W,
            padx=8,
            pady=3,
            font=("Segoe UI", 8),
        )
        self.lbl_sub_folder.grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=(6, 0), pady=(0, 4))

        # 5. File Info Frame (Icon, Size, Description)
        self.info_frame = tk.Frame(main_frame, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=14, pady=12)
        self.info_frame.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=(8, 12))

        # Left: Icon & Size
        icon_box = tk.Frame(self.info_frame, bg=CARD_BG)
        icon_box.pack(side=tk.LEFT, padx=(0, 16))

        # Native Windows registered default application icon for file extension (VLC, WinRAR, etc.)
        self.icon_label = tk.Label(icon_box, bg=CARD_BG)
        self.icon_label.pack()
        self._tk_icon = None
        self._update_app_icon(self.title)

        is_stream = any(d in self.url for d in ["youtube.com", "youtu.be", "tiktok.com", "vimeo.com"])
        if self.probed_size > 0:
            size_text = format_size_id(self.probed_size)
        elif is_stream:
            size_text = "Stream HD (1080p MP4)"
        elif self.is_probing and self.probed_size <= 0:
            size_text = "Memeriksa ukuran..."
        else:
            size_text = format_size_id(self.probed_size)

        self.lbl_size = tk.Label(icon_box, text=size_text, bg=CARD_BG, fg=FG_COLOR, font=("Segoe UI", 9, "bold"))
        self.lbl_size.pack(pady=(4, 0))

        # Right: Description box
        desc_box = tk.Frame(self.info_frame, bg=CARD_BG)
        desc_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(desc_box, text=tr("dlg_info_desc"), bg=CARD_BG, fg=THEME["text_secondary"], font=("Segoe UI", 8)).pack(anchor=tk.W)
        self.desc_entry = tk.Entry(
            desc_box,
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 9),
        )
        self.desc_entry.pack(fill=tk.X, expand=True, pady=(3, 0))

        # Parallel Connections indicator
        active_conns = settings.get_max_connections()
        if is_stream:
            conn_text = tr("dlg_info_accel_stream")
        else:
            conn_text = tr("dlg_info_accel_parallel", conns=active_conns)

        self.conn_label = tk.Label(
            desc_box,
            text=conn_text,
            bg=CARD_BG,
            fg=THEME["success"],
            font=("Segoe UI", 8, "italic"),
        )
        self.conn_label.pack(anchor=tk.W, pady=(6, 0))

        # 6. Action Buttons Row (Unduh Nanti, Mulai Unduh, Batal)
        self.btn_frame = tk.Frame(main_frame, bg=BG_COLOR)
        self.btn_frame.grid(row=6, column=0, columnspan=3, sticky=tk.E, pady=(4, 2))

        btn_later = create_modern_button(self.btn_frame, tr("dlg_info_download_later"), self._on_later, kind="secondary", padx=12, pady=4, radius=7)
        btn_later.pack(side=tk.LEFT, padx=4)

        btn_start = create_modern_button(self.btn_frame, tr("dlg_info_start_download"), self._on_start, kind="primary", padx=16, pady=4, radius=7)
        btn_start.pack(side=tk.LEFT, padx=4)
        btn_start.focus_set()  # Default button (Enter key triggers Mulai Unduh)

        btn_cancel = create_modern_button(self.btn_frame, tr("dlg_info_cancel"), self._on_cancel, kind="secondary", padx=12, pady=4, radius=7)
        btn_cancel.pack(side=tk.LEFT, padx=4)

        self.top.bind("<Return>", lambda e: self._on_start())
        self.top.bind("<Escape>", lambda e: self._on_cancel())

        main_frame.columnconfigure(1, weight=1)
        # Row 5 (info card) shouldn't blow up empty vertical space
        main_frame.rowconfigure(5, weight=0)

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
                is_stream = any(d in self.url for d in ["youtube.com", "youtu.be", "tiktok.com", "vimeo.com"])
                if size > 0:
                    self.lbl_size.config(text=format_size_id(size))
                elif is_stream:
                    self.lbl_size.config(text="Stream HD (1080p MP4)")
                elif self.is_probing and self.probed_size <= 0:
                    self.lbl_size.config(text=tr("dlg_info_probing"))
                else:
                    self.lbl_size.config(text=format_size_id(size))
                try:
                    is_packed = bool(self.lbl_size.pack_info())
                except Exception:
                    is_packed = False
                if not is_packed:
                    self.lbl_size.pack(pady=(2, 0))
        except Exception:
            pass

    def _on_add_category(self):
        try:
            from tkinter import simpledialog
            new_cat = simpledialog.askstring(tr("dlg_info_add_cat_title"), tr("dlg_info_add_cat_prompt"), parent=self.top)
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
        cat_disp = self.cat_var.get()
        self.category = get_canonical_category_key(cat_disp)
        cur_file = os.path.basename(self.path_var.get())
        self.cat_folder = settings.get_category_path(self.category)
        new_path = os.path.join(self.cat_folder, cur_file)
        self.path_var.set(new_path)
        self._update_app_icon(cur_file)
        if hasattr(self, "cb_remember") and self.cb_remember:
            self.cb_remember.config(text=tr("dlg_info_remember", cat=cat_disp))
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
            title=tr("dlg_info_browse_title"),
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
            self.remember_var.set(True)
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
        on_speed_limit_change: Optional[Callable[[int], None]] = None,
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
        self.on_speed_limit_change = on_speed_limit_change

        self.filename = os.path.basename(output_path) or "download.bin"
        self.show_details = True
        self.start_time = time.time()
        self.active_tab = 1

        self.speed_limit_enabled_var = tk.BooleanVar(master=self.parent, value=False)
        self.speed_limit_val_var = tk.StringVar(master=self.parent, value="512")
        self.cb_auto_close_var = tk.BooleanVar(master=self.parent, value=False)
        self.cb_shutdown_var = tk.BooleanVar(master=self.parent, value=False)
        self.cb_disconnect_var = tk.BooleanVar(master=self.parent, value=False)

        self._build_ui()

    def _build_ui(self):
        try:
            setup_global_ttk_theme()
        except Exception:
            pass

        self.top = tk.Toplevel(self.parent)
        apply_window_icon(self.top)
        self.top.title(f"0% {self.filename}")
        self.top.geometry("600x480")
        self.top.minsize(540, 420)
        self.top.configure(bg=THEME["surface"])
        self.top.protocol("WM_DELETE_WINDOW", self._on_cancel_click)

        # Center on screen and bring to front
        self.top.update_idletasks()
        try:
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            x = max(0, (screen_w - 600) // 2)
            y = max(0, (screen_h - 480) // 2)
            self.top.geometry(f"600x480+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.attributes("-topmost", True)
            self.top.after(500, lambda: self.top.attributes("-topmost", False))
            self.top.focus_force()
        except Exception:
            pass

        BG = THEME["surface"]
        FG = THEME["text_primary"]
        CARD_BG = THEME["surface_alt"]
        BORDER = THEME["border"]

        # Tab Header Row
        tab_frame = tk.Frame(self.top, bg=THEME["surface_alt"], padx=6, pady=4)
        tab_frame.pack(fill=tk.X)

        self.lbl_tab1 = tk.Label(
            tab_frame,
            text=tr("prog_tab_status"),
            bg=THEME["surface"],
            fg=FG,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            relief=tk.SOLID,
            bd=1,
            cursor="hand2",
        )
        self.lbl_tab1.pack(side=tk.LEFT, padx=2)
        self.lbl_tab1.bind("<Button-1>", lambda e: self._switch_tab(1))

        self.lbl_tab2 = tk.Label(
            tab_frame,
            text=tr("prog_tab_limiter"),
            bg=THEME["surface_alt"],
            fg=THEME["text_secondary"],
            font=("Segoe UI", 9),
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.lbl_tab2.pack(side=tk.LEFT, padx=2)
        self.lbl_tab2.bind("<Button-1>", lambda e: self._switch_tab(2))

        self.lbl_tab3 = tk.Label(
            tab_frame,
            text=tr("prog_tab_options"),
            bg=THEME["surface_alt"],
            fg=THEME["text_secondary"],
            font=("Segoe UI", 9),
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.lbl_tab3.pack(side=tk.LEFT, padx=2)
        self.lbl_tab3.bind("<Button-1>", lambda e: self._switch_tab(3))

        # Main Container for Tabs
        self.tab_container = tk.Frame(self.top, bg=BG)
        self.tab_container.pack(fill=tk.BOTH, expand=True)

        self.tab1_frame = tk.Frame(self.tab_container, bg=BG, padx=14, pady=10)
        self.tab1_frame.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Pembatas Kecepatan Frame
        self.tab2_frame = tk.Frame(self.tab_container, bg=BG, padx=16, pady=16)
        t2_card = tk.Frame(self.tab2_frame, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=14, pady=14)
        t2_card.pack(fill=tk.X, pady=(0, 14))

        cb_enable_limit = tk.Checkbutton(
            t2_card,
            text=tr("prog_limiter_enable"),
            variable=self.speed_limit_enabled_var,
            command=self._apply_speed_limit,
            bg=CARD_BG,
            fg=FG,
            selectcolor=THEME["input_bg"],
            activebackground=CARD_BG,
            activeforeground=FG,
            font=("Segoe UI", 10, "bold"),
        )
        cb_enable_limit.pack(anchor=tk.W, pady=(0, 10))

        rate_box = tk.Frame(t2_card, bg=CARD_BG)
        rate_box.pack(fill=tk.X, pady=(0, 10))

        tk.Label(rate_box, text=tr("prog_limiter_max"), bg=CARD_BG, fg=THEME["text_secondary"], font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
        self.entry_speed_limit = tk.Entry(
            rate_box,
            textvariable=self.speed_limit_val_var,
            bg=THEME["input_bg"],
            fg=FG,
            insertbackground=FG,
            relief=tk.SOLID,
            bd=1,
            width=10,
            font=("Segoe UI", 9, "bold"),
        )
        self.entry_speed_limit.pack(side=tk.LEFT, padx=(0, 6))
        self.entry_speed_limit.bind("<KeyRelease>", lambda e: self._apply_speed_limit())
        tk.Label(rate_box, text=tr("prog_unit_kbs"), bg=CARD_BG, fg=FG, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Presets
        tk.Label(t2_card, text=tr("prog_limiter_presets"), bg=CARD_BG, fg=THEME["text_secondary"], font=("Segoe UI", 8)).pack(anchor=tk.W, pady=(0, 4))
        presets_row = tk.Frame(t2_card, bg=CARD_BG)
        presets_row.pack(fill=tk.X, pady=(0, 10))
        for preset_kb, label_text in [(256, "256 KB/s"), (512, "512 KB/s"), (1024, "1 MB/s"), (2048, "2 MB/s"), (5120, "5 MB/s")]:
            btn = create_modern_button(presets_row, label_text, lambda kb=preset_kb: self._set_speed_preset(kb), kind="secondary", padx=8, pady=2, radius=6)
            btn.pack(side=tk.LEFT, padx=3)

        self.lbl_speed_limit_status = tk.Label(
            self.tab2_frame,
            text=tr("prog_limiter_status_off"),
            bg=BG,
            fg=THEME["text_secondary"],
            font=("Segoe UI", 8, "italic"),
        )
        self.lbl_speed_limit_status.pack(anchor=tk.W, pady=(4, 0))

        # Tab 3: Opsi saat selesai Frame
        self.tab3_frame = tk.Frame(self.tab_container, bg=BG, padx=16, pady=16)
        t3_card = tk.Frame(self.tab3_frame, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=14, pady=14)
        t3_card.pack(fill=tk.X, pady=(0, 14))

        tk.Label(t3_card, text=tr("prog_auto_actions"), bg=CARD_BG, fg=FG, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 8))

        tk.Checkbutton(
            t3_card,
            text=tr("prog_auto_close"),
            variable=self.cb_auto_close_var,
            bg=CARD_BG,
            fg=FG,
            selectcolor=THEME["input_bg"],
            activebackground=CARD_BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=3)

        tk.Checkbutton(
            t3_card,
            text=tr("prog_disconnect"),
            variable=self.cb_disconnect_var,
            bg=CARD_BG,
            fg=FG,
            selectcolor=THEME["input_bg"],
            activebackground=CARD_BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=3)

        tk.Checkbutton(
            t3_card,
            text=tr("prog_shutdown"),
            variable=self.cb_shutdown_var,
            bg=CARD_BG,
            fg=FG,
            selectcolor=THEME["input_bg"],
            activebackground=CARD_BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=3)

        tk.Label(
            self.tab3_frame,
            text=tr("prog_note_safe_shutdown"),
            bg=BG,
            fg=THEME["text_tertiary"],
            font=("Segoe UI", 8, "italic"),
        ).pack(anchor=tk.W, pady=(4, 0))

        # Build Tab 1 Content (Status Unduhan)
        content_frame = self.tab1_frame

        # Info Box (bordered dark card)
        info_box = tk.Frame(content_frame, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=12, pady=10)
        info_box.pack(fill=tk.X, pady=(0, 10))

        def add_info_row(row, label_text, default_val):
            tk.Label(info_box, text=label_text, bg=CARD_BG, fg=THEME["text_secondary"], font=("Segoe UI", 8), anchor=tk.W).grid(
                row=row, column=0, sticky=tk.W, pady=1
            )
            val_lbl = tk.Label(info_box, text=default_val, bg=CARD_BG, fg=FG, font=("Segoe UI", 8, "bold"), anchor=tk.W)
            val_lbl.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=1)
            return val_lbl

        disp_url = self.url if len(self.url) < 65 else self.url[:62] + "..."
        add_info_row(0, tr("prog_url"), disp_url)
        self.lbl_status = add_info_row(1, tr("prog_status"), tr("prog_receiving"))
        self.lbl_file_size = add_info_row(2, tr("prog_file_size"), format_size_id(self.total_bytes))
        self.lbl_downloaded = add_info_row(3, tr("prog_downloaded"), "0 B ( 0 % )")
        self.lbl_speed = add_info_row(4, tr("prog_transfer_rate"), f"0 B/{tr('prog_sec_unit')}")
        self.lbl_eta = add_info_row(5, tr("prog_time_left"), tr("prog_calculating"))
        add_info_row(6, tr("prog_resume_cap"), tr("prog_yes"))

        info_box.columnconfigure(1, weight=1)

        # Main Progress Bar
        bar_frame = tk.Frame(content_frame, bg=BG)
        bar_frame.pack(fill=tk.X, pady=(0, 8))

        self.progress_canvas = tk.Canvas(
            bar_frame,
            height=20,
            bg=THEME["input_bg"],
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.progress_canvas.pack(fill=tk.X)
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill=THEME["accent_primary"], outline="")
        self.progress_text = self.progress_canvas.create_text(260, 10, text="0%", fill="#ffffff", font=("Segoe UI", 9, "bold"))

        # Action Buttons
        btn_row = tk.Frame(content_frame, bg=BG)
        btn_row.pack(fill=tk.X, pady=(0, 10))

        self.btn_toggle = create_modern_button(btn_row, tr("prog_hide_details"), self._toggle_details, kind="secondary", padx=10, pady=3, radius=7)
        self.btn_toggle.pack(side=tk.LEFT)

        self.btn_cancel = create_modern_button(btn_row, tr("dlg_info_cancel"), self._on_cancel_click, kind="danger", padx=14, pady=3, radius=7)
        self.btn_cancel.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_pause = create_modern_button(btn_row, tr("tb_pause"), self._on_pause_click, kind="secondary", padx=14, pady=3, radius=7)
        self.btn_pause.pack(side=tk.RIGHT)

        # Detail Frame (Multi-segment visual bar + Connection table)
        self.detail_frame = tk.Frame(content_frame, bg=BG)
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            self.detail_frame,
            text=tr("prog_seg_progress"),
            bg=BG,
            fg=THEME["text_secondary"],
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, pady=(0, 3))

        # Segment Multi-connection Visualizer Canvas
        self.seg_canvas = tk.Canvas(
            self.detail_frame,
            height=22,
            bg=THEME["input_bg"],
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.seg_canvas.pack(fill=tk.X, pady=(0, 8))

        # Pre-create persistent canvas objects for zero-allocation rendering (replaces delete("all"))
        self.seg_bg_rects = []
        self.seg_fill_rects = []
        self.seg_dividers = []
        for i in range(self.parts):
            bg_id = self.seg_canvas.create_rectangle(0, 2, 0, 20, fill=CARD_BG, outline="")
            fill_id = self.seg_canvas.create_rectangle(0, 2, 0, 20, fill=THEME["accent_primary"], outline="")
            self.seg_bg_rects.append(bg_id)
            self.seg_fill_rects.append(fill_id)
            if i > 0:
                div_id = self.seg_canvas.create_line(0, 0, 0, 22, fill=BORDER, width=1)
                self.seg_dividers.append(div_id)

        # Connections Treeview
        tree_frame = tk.Frame(self.detail_frame, bg=BG)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.conn_tree = ttk.Treeview(tree_frame, columns=("num", "dl", "info"), show="headings", height=4)
        self.conn_tree.heading("num", text=tr("prog_col_conn"))
        self.conn_tree.heading("dl", text=tr("prog_col_dl"))
        self.conn_tree.heading("info", text=tr("prog_col_status"))

        self.conn_tree.column("num", width=75, anchor=tk.CENTER)
        self.conn_tree.column("dl", width=120, anchor=tk.E)
        self.conn_tree.column("info", width=220, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.conn_tree.yview)
        self.conn_tree.configure(yscrollcommand=tree_scroll.set)

        self.conn_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for i in range(1, self.parts + 1):
            self.conn_tree.insert("", "end", iid=str(i), values=(f"{tr('prog_col_conn')} {i}", "0 B", tr("prog_receiving")))

    def _toggle_details(self):
        if self.show_details:
            self.detail_frame.pack_forget()
            self.btn_toggle.config(text=tr("prog_show_details"))
            self.top.geometry("600x280")
            self.show_details = False
        else:
            self.detail_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_toggle.config(text=tr("prog_hide_details"))
            self.top.geometry("600x480")
            self.show_details = True
            self.top.geometry("600x480")
            self.show_details = True

    def _switch_tab(self, tab_num: int):
        self.active_tab = tab_num
        self.tab1_frame.pack_forget()
        self.tab2_frame.pack_forget()
        self.tab3_frame.pack_forget()

        for idx, lbl in enumerate([self.lbl_tab1, self.lbl_tab2, self.lbl_tab3], start=1):
            if idx == tab_num:
                lbl.config(bg=THEME["surface"], fg=THEME["text_primary"], relief=tk.SOLID, bd=1, font=("Segoe UI", 9, "bold"))
            else:
                lbl.config(bg=THEME["surface_alt"], fg=THEME["text_secondary"], relief=tk.FLAT, bd=0, font=("Segoe UI", 9))

        if tab_num == 1:
            self.tab1_frame.pack(fill=tk.BOTH, expand=True)
        elif tab_num == 2:
            self.tab2_frame.pack(fill=tk.BOTH, expand=True)
        elif tab_num == 3:
            self.tab3_frame.pack(fill=tk.BOTH, expand=True)

    def _set_speed_preset(self, kbps: int):
        self.speed_limit_enabled_var.set(True)
        self.speed_limit_val_var.set(str(kbps))
        self._apply_speed_limit()

    def _apply_speed_limit(self):
        if not self.speed_limit_enabled_var.get():
            limit_bps = 0
            if hasattr(self, "lbl_speed_limit_status"):
                self.lbl_speed_limit_status.config(text=tr("prog_limiter_status_off"), fg=THEME["text_secondary"])
        else:
            try:
                kbps = int(self.speed_limit_val_var.get().strip())
                limit_bps = max(1024, kbps * 1024)
            except Exception:
                limit_bps = 512 * 1024
                self.speed_limit_val_var.set("512")
            if hasattr(self, "lbl_speed_limit_status"):
                self.lbl_speed_limit_status.config(text=tr("prog_limiter_status_on", rate=limit_bps // 1024), fg=THEME["success"])
        if self.on_speed_limit_change:
            self.on_speed_limit_change(limit_bps)

    def _on_pause_click(self):
        pause_labels = ("Jeda", "Pause", tr("tb_pause"))
        resume_labels = ("Lanjutkan", "Resume", tr("tb_resume"))
        if self.btn_pause.cget("text") in resume_labels:
            if hasattr(self, "on_resume") and self.on_resume:
                self.on_resume(self.task_id)
            self.btn_pause.config(text=tr("tb_pause"))
            self.lbl_status.config(text=tr("prog_receiving"))
        else:
            if self.on_pause:
                self.on_pause(self.task_id)
            self.btn_pause.config(text=tr("tb_resume"))
            self.lbl_status.config(text=tr("status_paused"))
            self.lbl_speed.config(text=f"0 B/{tr('prog_sec_unit')}")
            self.lbl_eta.config(text=tr("status_paused"))

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
            resume_labels = ("Lanjutkan", "Resume", tr("tb_resume"))
            if self.btn_pause.cget("text") in resume_labels:
                # Currently paused, do not overwrite paused state
                return

            pct = 0.0
            if total_bytes > 0:
                pct = min(100.0, (bytes_downloaded / total_bytes) * 100)

            self.top.title(f"{int(pct)}% {self.filename}")

            self.lbl_file_size.config(text=format_size_id(total_bytes))
            self.lbl_downloaded.config(
                text=f"{format_size_id(bytes_downloaded)} ( {pct:.2f} % )"
            )
            self.lbl_speed.config(text=f"{format_size_id(int(speed_bps))}/{tr('prog_sec_unit')}")

            if speed_bps > 0 and total_bytes > bytes_downloaded:
                rem_sec = (total_bytes - bytes_downloaded) / speed_bps
                self.lbl_eta.config(text=format_time_left(rem_sec))
            elif pct >= 100.0:
                self.lbl_eta.config(text=tr("status_completed"))

            canvas_w = self.progress_canvas.winfo_width()
            if canvas_w <= 10:
                canvas_w = max(self.top.winfo_width() - 36, 520)
            fill_w = int(canvas_w * (pct / 100.0))
            self.progress_canvas.coords(self.progress_rect, 0, 0, fill_w, 20)
            self.progress_canvas.coords(self.progress_text, canvas_w // 2, 10)
            self.progress_canvas.itemconfig(self.progress_text, text=f"{pct:.1f}%")

            seg_w = self.seg_canvas.winfo_width()
            if seg_w <= 10:
                seg_w = max(self.top.winfo_width() - 36, 520)

            chunk_width = seg_w / max(1, self.parts)
            for i in range(self.parts):
                x0 = i * chunk_width
                x1 = (i + 1) * chunk_width
                if part_progress and i < len(part_progress):
                    p_data = part_progress[i]
                    p_dl = p_data.get("downloaded", 0)
                    p_tot = p_data.get("end_byte", 0) - p_data.get("start_byte", 0)
                    part_ratio = min(1.0, max(0.0, p_dl / p_tot)) if p_tot > 0 else min(1.0, max(0.0, pct / 100.0))
                else:
                    part_ratio = min(1.0, max(0.0, pct / 100.0))

                part_fill_w = chunk_width * part_ratio
                if i < len(self.seg_bg_rects):
                    self.seg_canvas.coords(self.seg_bg_rects[i], x0, 2, x1, 20)
                if i < len(self.seg_fill_rects):
                    self.seg_canvas.coords(self.seg_fill_rects[i], x0, 2, x0 + part_fill_w, 20)
                if i > 0 and (i - 1) < len(self.seg_dividers):
                    self.seg_canvas.coords(self.seg_dividers[i - 1], x0, 0, x0, 22)

            if part_progress:
                for p in part_progress:
                    iid = str(p.get("id"))
                    if self.conn_tree.exists(iid):
                        p_st = p.get("status") or tr("prog_receiving")
                        if p_st in ("Menerima data...", "Receiving data..."):
                            p_st = tr("prog_receiving")
                        self.conn_tree.item(iid, values=(f"{tr('prog_col_conn')} {iid}", format_size_id(p.get("downloaded", 0)), p_st))
            else:
                base_part = bytes_downloaded // max(1, self.parts)
                rem_part = bytes_downloaded % max(1, self.parts)
                for i in range(1, self.parts + 1):
                    iid = str(i)
                    if self.conn_tree.exists(iid):
                        per_part = base_part + (1 if i <= rem_part else 0)
                        self.conn_tree.item(iid, values=(f"{tr('prog_col_conn')} {i}", format_size_id(per_part), tr("prog_receiving")))
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
        apply_window_icon(self.top)
        self.top.title(tr("complete_title"))
        self.top.geometry("560x260")
        self.top.minsize(500, 230)
        self.top.resizable(True, False)
        self.top.configure(bg=THEME["surface"])

        self.top.update_idletasks()
        try:
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            x = max(0, (screen_w - 560) // 2)
            y = max(0, (screen_h - 260) // 2)
            self.top.geometry(f"560x260+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.attributes("-topmost", True)
            self.top.after(500, lambda: self.top.attributes("-topmost", False))
            self.top.focus_force()
        except Exception:
            pass

        BG = THEME["surface"]
        FG = THEME["text_primary"]
        CARD_BG = THEME["surface_alt"]
        BORDER = THEME["border"]

        content = tk.Frame(self.top, bg=BG, padx=16, pady=16)
        content.pack(fill=tk.BOTH, expand=True)

        hdr_frame = tk.Frame(content, bg=BG)
        hdr_frame.pack(fill=tk.X, pady=(0, 12))

        chk_canvas = tk.Canvas(hdr_frame, width=34, height=34, bg=BG, highlightthickness=0)
        chk_canvas.pack(side=tk.LEFT, padx=(0, 10))
        # Outer soft glow ring
        chk_canvas.create_oval(1, 1, 33, 33, fill="", outline="#10b981", width=1)
        # Inner emerald check circle
        chk_canvas.create_oval(3, 3, 31, 31, fill=THEME["success"], outline="")
        chk_canvas.create_line([10, 17, 15, 22, 24, 12], fill="#ffffff", width=2)

        tk.Label(
            hdr_frame,
            text=tr("complete_header"),
            bg=BG,
            fg=THEME["text_primary"],
            font=("Segoe UI", 12, "bold"),
        ).pack(side=tk.LEFT, anchor=tk.CENTER)

        det_box = tk.Frame(content, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=14, pady=10)
        det_box.pack(fill=tk.X, pady=(0, 14))

        tk.Label(det_box, text=f"{tr('col_name')}: {self.title}", bg=CARD_BG, fg=FG, font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(fill=tk.X)
        tk.Label(det_box, text=f"{tr('col_size')}: {format_size_id(self.total_bytes)}", bg=CARD_BG, fg=THEME["text_secondary"], font=("Segoe UI", 8), anchor=tk.W).pack(fill=tk.X, pady=(2, 0))
        tk.Label(det_box, text=f"{tr('tab_save_to')}: {self.output_path}", bg=CARD_BG, fg=THEME["text_tertiary"], font=("Segoe UI", 8), anchor=tk.W).pack(fill=tk.X, pady=(2, 0))

        btn_box = tk.Frame(content, bg=BG)
        btn_box.pack(fill=tk.X)

        self.btn_open = create_modern_button(btn_box, tr("complete_open_file"), self._on_open, kind="primary", padx=14, pady=4, radius=7)
        self.btn_open.pack(side=tk.RIGHT, padx=4)
        self.btn_open.focus_set()

        self.btn_folder = create_modern_button(btn_box, tr("complete_open_folder"), self._on_open_folder, kind="secondary", padx=12, pady=4, radius=7)
        self.btn_folder.pack(side=tk.RIGHT, padx=4)

        self.btn_done = create_modern_button(btn_box, tr("complete_done"), self.close, kind="secondary", padx=12, pady=4, radius=7)
        self.btn_done.pack(side=tk.RIGHT, padx=4)

        self.top.bind("<Return>", lambda e: self._on_open())
        self.top.bind("<Escape>", lambda e: self.close())

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

    def __init__(self, parent: tk.Tk, settings_manager=None, settings_mgr=None, on_save_callback=None):
        self.parent = parent
        self.sm = settings_mgr or settings_manager or settings
        self.on_save_callback = on_save_callback
        self.categories = [get_category_display_name(k) for k in CATEGORY_KEYS]
        self.conn_options = ["1", "2", "4", "8", "16", "24", "32"]
        self._build_ui()

    def _build_ui(self):
        try:
            setup_global_ttk_theme()
        except Exception:
            pass

        self.top = tk.Toplevel(self.parent)
        apply_window_icon(self.top)
        self.top.title(tr("dlg_opts_title"))
        self.top.geometry("620x590")
        self.top.minsize(580, 520)
        self.top.resizable(True, True)
        self.top.configure(bg=THEME["surface"])
        self.top.bind("<Escape>", lambda e: self.top.destroy())
        try:
            self.top.grab_set()
        except Exception:
            pass

        # Center on screen
        self.top.update_idletasks()
        try:
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            x = max(0, (screen_w - 620) // 2)
            y = max(0, (screen_h - 590) // 2)
            self.top.geometry(f"620x590+{x}+{y}")
            self.top.deiconify()
            self.top.lift()
            self.top.focus_force()
        except Exception:
            pass

        BG = THEME["surface"]
        FG = THEME["text_primary"]
        CARD_BG = THEME["surface_alt"]
        ENTRY_BG = THEME["input_bg"]
        BORDER = THEME["border"]

        main_frame = tk.Frame(self.top, bg=BG, padx=14, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Bottom Action buttons (Packed FIRST with side=tk.BOTTOM so they are ALWAYS guaranteed visible!)
        btn_box = tk.Frame(main_frame, bg=BG)
        btn_box.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self.btn_save = create_modern_button(btn_box, tr("btn_save"), self._on_save, kind="primary", padx=18, pady=5, radius=7)
        self.btn_save.pack(side=tk.RIGHT, padx=4)

        self.btn_cancel = create_modern_button(btn_box, tr("btn_cancel"), self.top.destroy, kind="secondary", padx=14, pady=5, radius=7)
        self.btn_cancel.pack(side=tk.RIGHT, padx=4)

        # Style the notebook
        style = ttk.Style()
        style.configure("Options.TNotebook", background=BG, borderwidth=0)
        style.configure("Options.TNotebook.Tab", background=CARD_BG, foreground=THEME["text_secondary"], padding=[12, 5], font=("Segoe UI", 9))
        style.map("Options.TNotebook.Tab", background=[("selected", BG)], foreground=[("selected", FG)])

        self.notebook = ttk.Notebook(main_frame, style="Options.TNotebook")
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # ---------------- TAB 1: UMUM (General) ----------------
        tab_general = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_general, text=tr("tab_general"))

        tk.Label(
            tab_general,
            text=tr("lbl_browser_integration"),
            bg=BG,
            fg=FG,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        browser_integration = self.sm.data.get("browser_integration", {})
        self.cb_chrome_var = tk.BooleanVar(value=browser_integration.get("chrome", True))
        self.cb_edge_var = tk.BooleanVar(value=browser_integration.get("edge", True))
        self.cb_firefox_var = tk.BooleanVar(value=browser_integration.get("firefox", True))
        self.cb_opera_var = tk.BooleanVar(value=browser_integration.get("opera", False))

        browsers_frame = tk.Frame(tab_general, bg=CARD_BG, relief=tk.SOLID, bd=1, padx=12, pady=8)
        browsers_frame.pack(fill=tk.X, pady=(0, 10))

        for idx, (name, var) in enumerate([
            ("Google Chrome", self.cb_chrome_var),
            ("Microsoft Edge", self.cb_edge_var),
            ("Mozilla Firefox", self.cb_firefox_var),
            ("Opera Browser", self.cb_opera_var),
        ]):
            r = idx // 2
            c = idx % 2
            tk.Checkbutton(
                browsers_frame,
                text=name,
                variable=var,
                bg=CARD_BG,
                fg=FG,
                selectcolor=ENTRY_BG,
                activebackground=CARD_BG,
                activeforeground=FG,
                font=("Segoe UI", 9),
            ).grid(row=r, column=c, sticky=tk.W, padx=10, pady=2)
        browsers_frame.columnconfigure(0, weight=1)
        browsers_frame.columnconfigure(1, weight=1)

        # Language selection row
        lang_frame = tk.Frame(tab_general, bg=BG)
        lang_frame.pack(fill=tk.X, pady=(2, 8))
        tk.Label(
            lang_frame,
            text=tr("lbl_language"),
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
            width=22,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        cur_lang = "English" if self.sm.get_language() == "en" else "Bahasa Indonesia"
        self.lang_var = tk.StringVar(value=cur_lang)
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["Bahasa Indonesia", "English"],
            state="readonly",
            width=18,
        )
        self.lang_combo.pack(side=tk.LEFT, padx=4)

        self.cb_startup_var = tk.BooleanVar(value=self.sm.get_autorun_startup())
        tk.Checkbutton(
            tab_general,
            text=tr("chk_autorun"),
            variable=self.cb_startup_var,
            bg=BG,
            fg=FG,
            selectcolor=ENTRY_BG,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=2)

        self.cb_close_tray_var = tk.BooleanVar(value=self.sm.get_close_to_tray())
        tk.Checkbutton(
            tab_general,
            text=tr("chk_close_tray"),
            variable=self.cb_close_tray_var,
            bg=BG,
            fg=FG,
            selectcolor=ENTRY_BG,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=2)

        self.cb_start_minimized_var = tk.BooleanVar(value=self.sm.get_start_minimized())
        tk.Checkbutton(
            tab_general,
            text=tr("chk_start_minimized"),
            variable=self.cb_start_minimized_var,
            bg=BG,
            fg=FG,
            selectcolor=ENTRY_BG,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=2)

        self.cb_sound_var = tk.BooleanVar(value=self.sm.get_play_sound_on_complete())
        tk.Checkbutton(
            tab_general,
            text=tr("chk_sound"),
            variable=self.cb_sound_var,
            bg=BG,
            fg=FG,
            selectcolor=ENTRY_BG,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=2)

        self.cb_confirm_del_var = tk.BooleanVar(value=self.sm.get_confirm_on_delete())
        tk.Checkbutton(
            tab_general,
            text=tr("chk_confirm_delete"),
            variable=self.cb_confirm_del_var,
            bg=BG,
            fg=FG,
            selectcolor=ENTRY_BG,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=2)

        self.cb_autoclose_progress_var = tk.BooleanVar(value=self.sm.get_autoclose_progress())
        tk.Checkbutton(
            tab_general,
            text=tr("chk_autoclose_progress"),
            variable=self.cb_autoclose_progress_var,
            bg=BG,
            fg=FG,
            selectcolor=ENTRY_BG,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=2)

        self.cb_clipboard_var = tk.BooleanVar(value=self.sm.data.get("monitor_clipboard", True))
        tk.Checkbutton(
            tab_general,
            text=tr("chk_clipboard"),
            variable=self.cb_clipboard_var,
            bg=BG,
            fg=FG,
            selectcolor=ENTRY_BG,
            activebackground=BG,
            activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W, pady=2)

        tk.Label(
            tab_general,
            text=tr("opt_ipc_port"),
            bg=BG,
            fg=THEME["success"],
            font=("Segoe UI", 8, "italic"),
        ).pack(anchor=tk.W, pady=(8, 0))

        # ---------------- TAB 2: JENIS BERKAS (File Types) ----------------
        tab_types = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_types, text=tr("tab_file_types"))

        tk.Label(
            tab_types,
            text=tr("opt_exts_lbl"),
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
            text=tr("opt_exceptions_lbl"),
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 4))

        self.exceptions_var = tk.StringVar(value=self.sm.data.get("exceptions", "*.speedtest.net *.fast.com"))
        self.exceptions_entry = tk.Entry(tab_types, textvariable=self.exceptions_var, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 9))
        self.exceptions_entry.pack(fill=tk.X, pady=(0, 4))
        tk.Label(tab_types, text=tr("opt_exceptions_hint"), bg=BG, fg=THEME["text_tertiary"], font=("Segoe UI", 8)).pack(anchor=tk.W)

        # ---------------- TAB 3: SIMPAN KE (Save To) ----------------
        tab_save = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_save, text=tr("tab_save_to"))

        tk.Label(
            tab_save,
            text=tr("opt_cat_folders_lbl"),
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 8))

        cat_frame = tk.Frame(tab_save, bg=BG)
        cat_frame.pack(fill=tk.X, pady=4)
        tk.Label(cat_frame, text=tr("opt_select_cat"), bg=BG, fg=FG, font=("Segoe UI", 9), width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.cat_var = tk.StringVar(value=self.categories[0])
        self.cat_combo = ttk.Combobox(cat_frame, textvariable=self.cat_var, values=self.categories, state="readonly", width=22)
        self.cat_combo.pack(side=tk.LEFT, padx=4)
        self.cat_combo.bind("<<ComboboxSelected>>", self._on_cat_change)

        path_frame = tk.Frame(tab_save, bg=BG)
        path_frame.pack(fill=tk.X, pady=(6, 14))
        tk.Label(path_frame, text=tr("opt_save_folder"), bg=BG, fg=FG, font=("Segoe UI", 9), width=15, anchor=tk.W).pack(side=tk.LEFT)
        initial_canon = get_canonical_category_key(self.categories[0])
        self.path_var = tk.StringVar(value=self.sm.get_category_path(initial_canon))
        self.path_entry = tk.Entry(path_frame, textvariable=self.path_var, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 9))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 6))

        self.btn_browse = create_modern_button(path_frame, "...", self._on_browse, kind="secondary", padx=8, pady=2, radius=6)
        self.btn_browse.pack(side=tk.RIGHT)

        # Temporary folder
        sep = tk.Frame(tab_save, bg=BORDER, height=1)
        sep.pack(fill=tk.X, pady=(0, 10))

        tk.Label(tab_save, text=tr("opt_temp_dir_lbl"), bg=BG, fg=FG, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 6))
        temp_frame = tk.Frame(tab_save, bg=BG)
        temp_frame.pack(fill=tk.X)
        self.temp_var = tk.StringVar(value=self.sm.data.get("temp_dir", os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")))
        self.temp_entry = tk.Entry(temp_frame, textvariable=self.temp_var, bg=ENTRY_BG, fg=FG, insertbackground=FG, relief=tk.SOLID, bd=1, font=("Segoe UI", 9))
        self.temp_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.btn_temp_browse = create_modern_button(temp_frame, "...", self._on_browse_temp, kind="secondary", padx=8, pady=2, radius=6)
        self.btn_temp_browse.pack(side=tk.RIGHT)

        # ---------------- TAB 4: KONEKSI (Connection) ----------------
        tab_conn = tk.Frame(self.notebook, bg=BG, padx=16, pady=16)
        self.notebook.add(tab_conn, text=tr("tab_connection"))

        tk.Label(
            tab_conn,
            text=tr("opt_conn_type_lbl"),
            bg=BG,
            fg=FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        conn_types = tr("opt_conn_types")
        if not isinstance(conn_types, (list, tuple)):
            conn_types = [
                "Kecepatan Tinggi: Sambungan Langsung (Ethernet/Kabel) / Wi-Fi / 4G",
                "Kecepatan Sedang: 3G / ADSL",
                "Kecepatan Rendah: Dial Up / VPN",
            ]
        conn_type_combo = ttk.Combobox(
            tab_conn,
            values=conn_types,
            state="readonly",
        )
        conn_type_combo.current(0)
        conn_type_combo.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            tab_conn,
            text=tr("opt_conn_max_lbl"),
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
        tk.Label(conn_frame, text=tr("opt_conn_channels"), bg=BG, fg=THEME["success"], font=("Segoe UI", 8, "italic")).pack(side=tk.LEFT)

        tk.Label(
            tab_conn,
            text=tr("opt_conn_note"),
            bg=BG,
            fg=THEME["text_tertiary"],
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, pady=(8, 0))

    def _on_cat_change(self, event=None):
        cat_disp = self.cat_var.get()
        canon_cat = get_canonical_category_key(cat_disp)
        self.path_var.set(self.sm.get_category_path(canon_cat))

    def _on_browse(self):
        try:
            self.top.grab_release()
        except Exception:
            pass

        initial_dir = self.path_var.get().strip() or os.path.expanduser("~/Downloads")
        chosen = filedialog.askdirectory(parent=self.top, initialdir=initial_dir, title=tr("opt_browse_cat_title"))

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
        chosen = filedialog.askdirectory(parent=self.top, initialdir=initial, title=tr("opt_browse_temp_title"))
        if chosen:
            self.temp_var.set(os.path.abspath(chosen))

    def _on_save(self):
        cat_disp = self.cat_var.get()
        canon_cat = get_canonical_category_key(cat_disp)
        p = self.path_var.get().strip()
        if p:
            self.sm.set_category_path(canon_cat, os.path.abspath(p))

        # Save connection limit
        try:
            val = int(self.conn_var.get())
            self.sm.set_max_connections(val)
        except Exception:
            pass

        # Save browser integration, autorun, tray and system settings
        try:
            chosen_l = self.lang_var.get().strip().lower()
            new_lang = "en" if "english" in chosen_l else "id"
            self.sm.set_language(new_lang)
            self.sm.data["browser_integration"] = {
                "chrome": bool(self.cb_chrome_var.get()),
                "edge": bool(self.cb_edge_var.get()),
                "firefox": bool(self.cb_firefox_var.get()),
                "opera": bool(self.cb_opera_var.get()),
            }
            self.sm.set_autorun_startup(bool(self.cb_startup_var.get()))
            self.sm.set_close_to_tray(bool(self.cb_close_tray_var.get()))
            self.sm.set_start_minimized(bool(self.cb_start_minimized_var.get()))
            self.sm.set_play_sound_on_complete(bool(self.cb_sound_var.get()))
            self.sm.set_confirm_on_delete(bool(self.cb_confirm_del_var.get()))
            self.sm.set_autoclose_progress(bool(self.cb_autoclose_progress_var.get()))
            self.sm.data["monitor_clipboard"] = bool(self.cb_clipboard_var.get())
            self.sm.data["file_types"] = self.exts_entry.get("1.0", tk.END).strip()
            self.sm.data["exceptions"] = self.exceptions_var.get().strip()
            self.sm.data["temp_dir"] = self.temp_var.get().strip()
            self.sm._save()

            if self.on_save_callback:
                self.on_save_callback(new_lang)
        except Exception:
            pass

        self.top.destroy()
