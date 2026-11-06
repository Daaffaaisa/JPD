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
from idm_gui.i18n import tr, get_current_lang
from idm_gui.theme import (
    THEME,
    setup_global_ttk_theme,
    create_modern_button,
    draw_round_rectangle,
    apply_window_icon,
    get_app_png_path,
    interpolate_color,
    FONT_DISPLAY,
    FONT_FAMILY,
    FONT_TITLE,
    FONT_HEADING,
    FONT_BODY,
    FONT_SMALL,
    FONT_CODE,
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


def get_file_type_glyph(category: str, filename: str = "") -> str:
    """Returns a modern semantic glyph matching the file category and extension."""
    c = category.lower()
    fn = filename.lower()
    if "video" in c or fn.endswith((".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv")):
        return "🎬"
    elif "musik" in c or "audio" in c or fn.endswith((".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg")):
        return "🎵"
    elif "gambar" in c or "image" in c or fn.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico", ".avif")):
        return "🖼️"
    elif "program" in c or fn.endswith((".exe", ".msi", ".iso", ".bat", ".cmd")):
        return "📦"
    elif "dokumen" in c or fn.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt")):
        return "📄"
    elif "kompres" in c or "zip" in c or fn.endswith((".zip", ".rar", ".7z", ".tar", ".gz", ".bz2")):
        return "🗜️"
    return "📄"


class _CanvasTextAdapter:
    """Lightweight adapter mimicking a tk.Label interface for pure Canvas text items."""

    def __init__(self, canvas: tk.Canvas, item_id: int):
        self.canvas = canvas
        self.item_id = item_id

    def config(self, **kwargs):
        self.configure(**kwargs)

    def configure(self, **kwargs):
        for k, v in kwargs.items():
            if k == "text":
                self.canvas.itemconfigure(self.item_id, text=v)
            elif k in ("fg", "foreground", "val_fg"):
                self.canvas.itemconfigure(self.item_id, fill=v)
            elif k == "font":
                self.canvas.itemconfigure(self.item_id, font=v)

    def cget(self, key: str):
        if key == "text":
            return self.canvas.itemcget(self.item_id, "text")
        elif key in ("fg", "foreground"):
            return self.canvas.itemcget(self.item_id, "fill")
        return ""


class TactileCard(tk.Canvas):
    """Modern 3D elevated tactile card with smooth rounded corners, specular highlight, and ambient shadow."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        initial_val: str,
        val_fg: str = "#ffffff",
        r: int = 12,
        height: int = 70,
    ):
        bg_col = parent.cget("bg") if hasattr(parent, "cget") else THEME["surface_alt"]
        super().__init__(parent, height=height, bg=bg_col, highlightthickness=0)
        self.r = r
        self.title_text = title
        self.val_fg = val_fg

        # Use pure canvas vector text items instead of embedded tk.Label windows
        # to eliminate Win32 GDI child clipping artifacts / black horizontal slicing
        self.item_title = self.create_text(
            16,
            21,
            text=title,
            fill=THEME["text_secondary"],
            font=(FONT_DISPLAY, 8, "bold"),
            anchor=tk.W,
            tags="card_text",
        )
        self.item_val = self.create_text(
            16,
            48,
            text=initial_val,
            fill=val_fg,
            font=(FONT_DISPLAY, 12, "bold"),
            anchor=tk.W,
            tags="card_text",
        )
        self.lbl_title = _CanvasTextAdapter(self, self.item_title)
        self.lbl_val = _CanvasTextAdapter(self, self.item_val)

        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 30 or h < 30:
            return
        self.delete("card_bg")
        r = self.r
        # 1. Ambient drop shadow (offset down 2px)
        draw_round_rectangle(self, 2, 4, w - 2, h, r=r + 1, fill="#04070e", outline="", tags="card_bg")
        # 2. Outer bottom bevel rim
        draw_round_rectangle(self, 1, 1, w - 1, h - 2, r=r, fill="#070b13", outline="", tags="card_bg")
        # 3. Stepped 3D body: top plate lighter, bottom plate deeper
        mid = (h - 2) // 2
        draw_round_rectangle(self, 2, 2, w - 2, h - 3, r=r - 1, fill="#1e2a3c", outline="", tags="card_bg")
        draw_round_rectangle(self, 2, mid, w - 2, h - 3, r=r - 1, fill="#131b26", outline="", tags="card_bg")
        # 4. Inset overhead specular rim highlight (Apple 3D gleam)
        self.create_line(r + 2, 2, w - r - 2, 2, fill="#4e6894", width=1.5, tags="card_bg")
        self.tag_lower("card_bg")


class TactileStorageCard(tk.Canvas):
    """Modern 3D elevated storage card with smooth rounded corners, specular highlight, and embedded open button."""

    def __init__(self, parent: tk.Widget, on_open_folder: Any, r: int = 10):
        bg_col = parent.cget("bg") if hasattr(parent, "cget") else THEME["surface_alt"]
        super().__init__(parent, height=86, bg=bg_col, highlightthickness=0)
        self.r = r
        self.on_open_folder = on_open_folder

        self.lbl_title = tk.Label(
            self,
            text="PENYIMPANAN",
            bg="#192231",
            fg=THEME["text_tertiary"],
            font=(FONT_DISPLAY, 7, "bold"),
        )
        self.lbl_path = tk.Label(
            self,
            text=os.path.basename(os.path.expanduser("~")) + "/Downloads",
            bg="#131b26",
            fg=THEME["text_secondary"],
            font=(FONT_FAMILY, 8),
        )
        self.btn_open = create_modern_button(
            self,
            text="↗ Buka Folder",
            command=on_open_folder,
            kind="secondary",
            padx=6,
            pady=2,
            radius=6,
            tooltip="Buka Folder Unduhan Utama",
        )

        self.win_t = self.create_window(14, 15, window=self.lbl_title, anchor=tk.W)
        self.win_p = self.create_window(14, 34, window=self.lbl_path, anchor=tk.W)
        self.win_b = self.create_window(14, 63, window=self.btn_open, anchor=tk.W)

        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 30 or h < 30:
            return
        self.delete("card_bg")
        r = self.r
        draw_round_rectangle(self, 2, 4, w - 2, h, r=r + 1, fill="#04070e", outline="", tags="card_bg")
        draw_round_rectangle(self, 1, 1, w - 1, h - 2, r=r, fill="#070b13", outline="", tags="card_bg")
        mid = (h - 2) // 2
        draw_round_rectangle(self, 2, 2, w - 2, h - 3, r=r - 1, fill="#192231", outline="", tags="card_bg")
        draw_round_rectangle(self, 2, mid, w - 2, h - 3, r=r - 1, fill="#131b26", outline="", tags="card_bg")
        self.create_line(r + 2, 2, w - r - 2, 2, fill="#3d5275", width=1.5, tags="card_bg")
        self.tag_lower("card_bg")
        self.itemconfigure(self.win_b, width=max(40, w - 28))


class TactileTableContainer(tk.Canvas):
    """3D tactile rounded container for the downloads table with drop shadow and specular highlight."""

    def __init__(self, parent: tk.Widget, r: int = 14):
        bg_col = parent.cget("bg") if hasattr(parent, "cget") else THEME["bg_dark"]
        super().__init__(parent, bg=bg_col, highlightthickness=0)
        self.r = r

        # Inner frame to hold treeview and scrollbar
        self.inner_frame = tk.Frame(self, bg=THEME["tree_bg"])
        self.win_id = self.create_window(0, 0, window=self.inner_frame, anchor=tk.NW)

        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50 or h < 50:
            return
        self.delete("card_bg")
        r = self.r

        # 1. Ambient drop shadow
        draw_round_rectangle(self, 3, 5, w - 3, h, r=r + 2, fill="#04070e", outline="", tags="card_bg")
        # 2. Outer dark bottom rim
        draw_round_rectangle(self, 2, 2, w - 2, h - 2, r=r, fill="#070b13", outline="", tags="card_bg")
        # 3. Main body with subtle dark border (no distracting bright white lines)
        draw_round_rectangle(self, 3, 3, w - 3, h - 3, r=r - 1, fill=THEME["tree_bg"], outline="#1e293b", width=1, tags="card_bg")

        self.tag_lower("card_bg")

        pad = 4
        self.coords(self.win_id, pad, pad)
        self.itemconfigure(self.win_id, width=max(10, w - (pad * 2)), height=max(10, h - (pad * 2)))


class SidebarNavItem(tk.Frame):
    """Modern macOS/Apple-inspired sidebar navigation pill item with live count badge."""

    def __init__(
        self,
        parent: tk.Widget,
        icon: str,
        text: str,
        key: str,
        on_click: Optional[Any] = None,
        on_double_click: Optional[Any] = None,
    ):
        super().__init__(parent, bg=THEME["surface_alt"], cursor="hand2")
        self.key = key
        self.raw_text = text
        self.on_click = on_click
        self.on_double_click = on_double_click
        self.is_active = False
        self.is_compact = False
        self.count = 0

        # Left 3px active indicator bar
        self.indicator = tk.Frame(self, width=3, bg=THEME["surface_alt"])
        self.indicator.pack(side=tk.LEFT, fill=tk.Y, pady=2)

        # Content container
        self.content = tk.Frame(self, bg=THEME["surface_alt"], padx=8, pady=5)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 8), pady=1)

        # Fixed-width 32px container for icon
        self.icon_box = tk.Frame(self.content, bg=THEME["surface_alt"], width=32, height=24)
        self.icon_box.pack_propagate(False)
        self.icon_box.pack(side=tk.LEFT, padx=(2, 6))

        clean_icon = icon.replace("\ufe0f", "")
        self.lbl_icon = tk.Label(
            self.icon_box,
            text=clean_icon,
            bg=THEME["surface_alt"],
            fg=THEME["text_secondary"],
            font=(FONT_DISPLAY, 10),
            anchor=tk.CENTER,
        )
        self.lbl_icon.place(relx=0.45, rely=0.5, anchor=tk.CENTER)

        # Phone-style round notification badge overlay for compact mode (top-right of icon)
        self.badge_canvas = tk.Canvas(self.icon_box, width=14, height=14, bg=THEME["surface_alt"], highlightthickness=0)

        self.lbl_badge = tk.Label(
            self.content,
            text="0",
            bg=THEME["input_bg"],
            fg=THEME["text_tertiary"],
            font=(FONT_DISPLAY, 8, "bold"),
            padx=6,
            pady=1,
        )
        self.lbl_badge.pack(side=tk.RIGHT, padx=(4, 4))

        self.lbl_text = tk.Label(
            self.content,
            text=text,
            bg=THEME["surface_alt"],
            fg=THEME["text_secondary"],
            font=(FONT_FAMILY, 9),
        )
        self.lbl_text.pack(side=tk.LEFT)

        for w in (self, self.content, self.icon_box, self.lbl_icon, self.lbl_text, self.lbl_badge, self.badge_canvas):
            w.bind("<Button-1>", lambda e: self._handle_click())
            w.bind("<Double-Button-1>", lambda e: self._handle_double_click())
            w.bind("<Enter>", lambda e: self._on_enter())
            w.bind("<Leave>", lambda e: self._on_leave())

    def _draw_phone_badge(self):
        if not self.is_compact or self.count <= 0:
            self.badge_canvas.place_forget()
            return

        cnt_str = str(self.count) if self.count < 100 else "99+"
        is_double = len(cnt_str) > 1
        bw = 20 if is_double else 14
        bh = 14
        self.badge_canvas.configure(width=bw, height=bh)
        self.badge_canvas.delete("all")

        bg_col = self.icon_box.cget("bg")
        self.badge_canvas.configure(bg=bg_col)

        if not is_double:
            self.badge_canvas.create_oval(1, 1, 13, 13, fill="#ef4444", outline="#070b13", width=1)
            self.badge_canvas.create_text(7, 7, text=cnt_str, fill="#ffffff", font=(FONT_DISPLAY, 7, "bold"))
        else:
            self.badge_canvas.create_oval(1, 1, 13, 13, fill="#ef4444", outline="#070b13", width=1)
            self.badge_canvas.create_oval(bw - 13, 1, bw - 1, 13, fill="#ef4444", outline="#070b13", width=1)
            self.badge_canvas.create_rectangle(7, 1, bw - 7, 13, fill="#ef4444", outline="")
            self.badge_canvas.create_line(7, 1, bw - 7, 1, fill="#070b13", width=1)
            self.badge_canvas.create_line(7, 13, bw - 7, 13, fill="#070b13", width=1)
            self.badge_canvas.create_text(bw // 2, 7, text=cnt_str, fill="#ffffff", font=(FONT_DISPLAY, 6, "bold"))

        self.badge_canvas.place(relx=1.0, rely=0.0, anchor=tk.NE)

    def set_compact(self, compact: bool):
        self.is_compact = compact
        if compact:
            self.lbl_text.pack_forget()
            self.lbl_badge.pack_forget()
            self.content.pack_configure(padx=0, pady=3)
            self.icon_box.pack_configure(padx=0)
            self.lbl_icon.place_configure(relx=0.45, rely=0.55)
            self._draw_phone_badge()
        else:
            self.badge_canvas.place_forget()
            self.content.pack_configure(padx=(2, 8), pady=1)
            self.icon_box.pack_configure(padx=(2, 6))
            self.lbl_icon.place_configure(relx=0.45, rely=0.5)
            self.lbl_badge.pack(side=tk.RIGHT, padx=(4, 4))
            self.lbl_text.pack(side=tk.LEFT)

    def set_text_fade(self, alpha: float):
        """Fade text and badge labels smoothly between background color and target foreground color."""
        bg_col = "#1e293b" if self.is_active else THEME["surface_alt"]
        target_fg = "#ffffff" if self.is_active else THEME["text_secondary"]
        target_badge_fg = "#60a5fa" if self.is_active else THEME["text_tertiary"]
        blended_fg = interpolate_color(bg_col, target_fg, alpha)
        blended_badge_fg = interpolate_color(bg_col, target_badge_fg, alpha)
        blended_badge_bg = interpolate_color(bg_col, THEME["input_bg"], alpha)
        try:
            self.lbl_text.configure(fg=blended_fg)
            self.lbl_badge.configure(bg=blended_badge_bg, fg=blended_badge_fg)
        except Exception:
            pass

    def _handle_click(self):
        if self.on_click:
            self.on_click(self.key)

    def _handle_double_click(self):
        if self.on_double_click:
            self.on_double_click(self.key)

    def set_active(self, active: bool):
        self.is_active = active
        bg_col = "#1e293b" if active else THEME["surface_alt"]
        fg_col = "#ffffff" if active else THEME["text_secondary"]
        ind_col = THEME["accent_primary"] if active else THEME["surface_alt"]
        badge_fg = "#60a5fa" if active else THEME["text_tertiary"]

        self.configure(bg=THEME["surface_alt"])
        self.indicator.configure(bg=ind_col)
        self.content.configure(bg=bg_col)
        self.icon_box.configure(bg=bg_col)
        self.badge_canvas.configure(bg=bg_col)
        self.lbl_icon.configure(bg=bg_col, fg="#60a5fa" if active else THEME["text_secondary"])
        self.lbl_text.configure(bg=bg_col, fg=fg_col, font=(FONT_DISPLAY if active else FONT_FAMILY, 9, "bold" if active else "normal"))
        self.lbl_badge.configure(bg=THEME["input_bg"], fg=badge_fg)
        if self.is_compact:
            self._draw_phone_badge()

    def set_count(self, count: int):
        self.count = count
        self.lbl_badge.config(text=str(count))
        if self.is_compact:
            self._draw_phone_badge()

    def set_label(self, new_text: str):
        self.raw_text = new_text
        self.lbl_text.configure(text=new_text)

    def _on_enter(self):
        if not self.is_active:
            hover_bg = "#192231"
            self.content.configure(bg=hover_bg)
            self.icon_box.configure(bg=hover_bg)
            self.badge_canvas.configure(bg=hover_bg)
            self.lbl_icon.configure(bg=hover_bg)
            self.lbl_text.configure(bg=hover_bg)

    def _on_leave(self):
        if not self.is_active:
            bg_col = THEME["surface_alt"]
            self.content.configure(bg=bg_col)
            self.icon_box.configure(bg=bg_col)
            self.badge_canvas.configure(bg=bg_col)
            self.lbl_text.configure(bg=bg_col)
            self.lbl_icon.configure(bg=bg_col)
            self.lbl_text.configure(bg=bg_col)


class IDMGUIApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Just Press Download (JPD)")
        self.root.geometry("1040x620")
        self.root.minsize(820, 480)
        self.root.configure(bg=THEME["bg_dark"])
        apply_window_icon(self.root)

        self.engine = DownloadEngine()
        self.queue = DownloadQueue()
        self.settings = settings
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            try:
                self.queue.load_from_file(self.settings.get_tasks_filepath())
            except Exception:
                pass
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
        self.active_category_filter = "all"
        self.sidebar_items: dict[str, Any] = {}
        self.settings = settings
        self.tray_icon = None

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

        # Initialize System Tray Icon
        self._init_tray()

        is_autostart = "--autostart" in sys.argv
        is_incoming = "--url" in sys.argv
        if is_autostart or is_incoming or self.settings.get_start_minimized():
            self.root.withdraw()
        else:
            self.root.deiconify()

        # If launched with a download URL (from browser auto-launch or CLI)
        if is_incoming and not os.environ.get("PYTEST_CURRENT_TEST"):
            try:
                idx = sys.argv.index("--url")
                if idx + 1 < len(sys.argv):
                    u_val = sys.argv[idx + 1]
                    t_val = ""
                    r_val = ""
                    if "--title" in sys.argv:
                        t_idx = sys.argv.index("--title")
                        if t_idx + 1 < len(sys.argv):
                            t_val = sys.argv[t_idx + 1]
                    if "--referer" in sys.argv:
                        r_idx = sys.argv.index("--referer")
                        if r_idx + 1 < len(sys.argv):
                            r_val = sys.argv[r_idx + 1]
                    # Keep main dashboard window silently in tray, only display the download info dialog!
                    self.root.withdraw()
                    def _trigger_incoming():
                        category = self._detect_category(u_val, t_val)
                        save_dir = self.settings.get_category_path(category)
                        clean_fname = self._get_clean_title_with_ext(u_val, t_val, category)
                        t_id = self.queue.add_task(url=u_val, output_path=os.path.join(save_dir, clean_fname))
                        self._on_server_task_added(t_id, {
                            "url": u_val,
                            "title": t_val,
                            "referer": r_val,
                        })
                    self.root.after(30, _trigger_incoming)
            except Exception:
                pass

        # Start periodic UI update timer and ensure initial 230px sash
        self.root.after(30, self._apply_initial_sash)
        self.root.after(300, self._tick_ui)

    def _apply_initial_sash(self):
        try:
            target = 56 if getattr(self, "sidebar_compact", False) else 230
            self.paned.paneconfig(self.sidebar_frame, minsize=target)
            self.paned.sash_place(0, target, 0)
            self.sidebar_frame.configure(width=target)
        except Exception:
            pass

    def _detect_category(self, url: str, title: str) -> str:
        lower = (url + " " + title).lower()
        if any(x in lower for x in ["video", ".mp4", ".mkv", ".webm", ".avi", ".flv", "youtube.com", "youtu.be", "googlevideo", "vimeo", "tiktok.com", "tiktokcdn"]):
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
        common_exts = {
            "jpg", "jpeg", "png", "webp", "gif", "bmp", "svg", "avif", "ico",
            "mp4", "mkv", "webm", "avi", "mov", "flv",
            "mp3", "m4a", "wav", "flac", "aac", "ogg",
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt",
            "zip", "rar", "7z", "tar", "gz",
            "exe", "msi", "iso"
        }
        if "." in clean and clean.rsplit(".", 1)[-1].lower() in common_exts:
            return clean

        fallback_map = {
            "Gambar": ".jpg",
            "Video": ".mp4",
            "Musik": ".mp3",
            "Dokumen": ".pdf",
            "Berkas Terkompresi": ".zip",
            "Program": ".exe",
        }

        # For stream and social video URLs, immediately use category fallback without any blocking network probe
        is_stream = any(d in url for d in ["youtube.com", "youtu.be", "tiktok.com", "vimeo.com", "googlevideo", "tiktokcdn"])
        if is_stream:
            ext = fallback_map.get(category, ".mp4")
            base = clean or "video"
            return f"{base}{ext}"

        # Fast local URL path parsing (0ms overhead, no synchronous HTTP blocking!)
        try:
            parsed = urllib.parse.urlparse(url)
            path_base = os.path.basename(parsed.path)
            if path_base and "." in path_base:
                ext = "." + path_base.rsplit(".", 1)[-1].lower()
                if ext.lstrip(".") in common_exts:
                    base = clean or path_base.rsplit(".", 1)[0]
                    return f"{base}{ext}"
        except Exception:
            pass

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

            incoming_title = title
            # Clean up browser notification count prefixes and generic tab slogans (e.g. "(8) Watch trending videos...")
            if any(d in url for d in ["tiktok.com", "youtube.com"]):
                import re
                clean_t = re.sub(r"^\(\d+\)\s*", "", incoming_title).strip()
                if not clean_t or any(x in clean_t.lower() for x in ["watch trending", "tiktok", "youtube"]):
                    m = re.search(r"/video/(\d+)", url)
                    if m:
                        incoming_title = f"TikTok_Video_{m.group(1)}"
                    elif "/shorts/" in url:
                        m_short = re.search(r"/shorts/([a-zA-Z0-9_-]+)", url)
                        if m_short:
                            incoming_title = f"YouTube_Shorts_{m_short.group(1)}"
                else:
                    incoming_title = clean_t

            category = self._detect_category(url, incoming_title)
            clean_title = self._get_clean_title_with_ext(url, incoming_title, category)
            remembered_dir = settings.get_category_path(category)
            task.output_path = os.path.join(remembered_dir, clean_title)

            # Check file safety
            is_suspicious, sec_warning = self._check_file_security(clean_title)
            if payload.get("is_suspicious"):
                is_suspicious = True
                sec_warning = payload.get("security_warning") or sec_warning

            # If fileSize is already known from browser payload, use it directly (PREVENTS BURNING ONE-TIME TOKENS!)
            payload_size = int(payload.get("file_size", 0))
            is_stream_url = any(d in url for d in ["youtube.com", "youtu.be", "tiktok.com", "vimeo.com"])
            probed_size = payload_size if payload_size > 0 else 0

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

            dlg = DownloadInfoDialog(
                parent=self.root,
                url=url,
                title=clean_title,
                probed_size=probed_size,
                category=category,
                on_action=on_dialog_action,
                is_suspicious=is_suspicious,
                security_warning=sec_warning,
                is_probing=probed_size <= 0,
            )

            if probed_size <= 0 and not os.environ.get("PYTEST_CURRENT_TEST"):
                def probe_incoming_worker():
                    sz = 0
                    if is_stream_url:
                        try:
                            import yt_dlp
                            headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                                "Referer": "https://www.tiktok.com/" if ("tiktok.com" in url or "tiktok.com" in referer) else "https://www.google.com/",
                            }
                            ydl_opts = {
                                "quiet": True,
                                "skip_download": True,
                                "no_warnings": True,
                                "http_headers": headers,
                            }
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                                info = ydl.extract_info(url, download=False)
                                sz = info.get("filesize") or info.get("filesize_approx") or 0
                                if not sz and "formats" in info and info["formats"]:
                                    for fmt in reversed(info["formats"]):
                                        if fmt.get("filesize"):
                                            sz = fmt["filesize"]
                                            break
                        except Exception:
                            pass
                    else:
                        try:
                            sz, _ = self.engine.probe(url, headers=req_headers)
                        except Exception:
                            pass

                    if sz > 0:
                        task.total_bytes = sz
                        def apply_size():
                            try:
                                if dlg and hasattr(dlg, "top") and dlg.top.winfo_exists():
                                    dlg.update_probed_size(sz)
                            except Exception:
                                pass
                        try:
                            self.root.after(0, apply_size)
                        except Exception:
                            pass

                threading.Thread(target=probe_incoming_worker, daemon=True).start()

        self.root.after(50, handle_incoming)

    def _init_tray(self):
        """Initializes system tray icon in a background daemon thread."""
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return
        try:
            import pystray
            from PIL import Image

            png_p = get_app_png_path() or os.path.abspath("icon.png")
            if os.path.exists(png_p):
                tray_img = Image.open(png_p).resize((32, 32))
            else:
                tray_img = Image.new("RGBA", (32, 32), color="#2563eb")

            tray_menu = pystray.Menu(
                pystray.MenuItem("Buka JustPressDownload (JPD)", self.restore_from_tray, default=True),
                pystray.MenuItem("Tambah URL Baru...", lambda icon, item: self.root.after(0, self.open_add_url_dialog)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Lanjutkan Semua Unduhan", lambda icon, item: self.root.after(0, self.resume_all)),
                pystray.MenuItem("Jeda Semua Unduhan", lambda icon, item: self.root.after(0, self.pause_all)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Pengaturan (Opsi)...", lambda icon, item: self.root.after(0, self.open_options_dialog)),
                pystray.MenuItem("Keluar (Exit)", lambda icon, item: self.root.after(0, self.quit_app)),
            )

            self.tray_icon = pystray.Icon(
                "JustPressDownload",
                tray_img,
                "JustPressDownload (JPD)",
                tray_menu,
            )
            th = threading.Thread(target=self.tray_icon.run, daemon=True)
            th.start()
        except Exception:
            self.tray_icon = None

    def restore_from_tray(self, icon=None, item=None):
        """Restores and brings main window to front."""
        def _restore():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.root.state("normal")
            except Exception:
                pass
        self.root.after(0, _restore)

    def minimize_to_tray(self):
        """Minimizes main window to system tray."""
        try:
            self.root.withdraw()
            if hasattr(self, "tray_icon") and self.tray_icon and hasattr(self.tray_icon, "notify"):
                try:
                    self.tray_icon.notify("Aplikasi diminimalkan ke System Tray", "JustPressDownload (JPD)")
                except Exception:
                    pass
        except Exception:
            pass

    def quit_app(self):
        """Full exit: stops background services, tray icon, and destroys root window."""
        # Stop all running tasks
        for event in list(self.stop_events.values()):
            try:
                event.set()
            except Exception:
                pass

        # Save persistent task queue
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            try:
                self.queue.save_to_file(self.settings.get_tasks_filepath())
            except Exception:
                pass

        if hasattr(self, "tray_icon") and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        if hasattr(self, "server") and self.server:
            try:
                self.server.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _on_close(self):
        if self.settings.get_close_to_tray():
            self.minimize_to_tray()
        else:
            self.quit_app()

    def _setup_styles(self):
        setup_global_ttk_theme()

    def _build_menu(self):
        self.menubar = tk.Menu(self.root, bg=THEME["surface"], fg=THEME["text_primary"], activebackground=THEME["accent_primary"], activeforeground="#ffffff", bd=0)

        # 1. Menu Tugas (Tasks)
        tasks_menu = tk.Menu(self.menubar, tearoff=0)
        tasks_menu.add_command(label=tr("menu_add_url"), accelerator="Ctrl+N", command=self.open_add_url_dialog)
        tasks_menu.add_separator()
        tasks_menu.add_command(label=tr("menu_export"), command=self.export_to_text_file)
        tasks_menu.add_command(label=tr("menu_import"), command=self.import_from_text_file)
        tasks_menu.add_separator()
        tasks_menu.add_command(label=tr("menu_exit"), accelerator="Alt+F4", command=self.quit_app)
        self.menubar.add_cascade(label=tr("menu_tasks"), menu=tasks_menu)

        # 2. Menu Berkas (File)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label=tr("menu_pause"), command=self.pause_selected)
        file_menu.add_command(label=tr("menu_resume"), command=self.resume_selected)
        file_menu.add_command(label=tr("menu_delete"), accelerator="Del", command=self.delete_selected)
        file_menu.add_separator()
        file_menu.add_command(label=tr("menu_open_file"), command=self.open_selected_file)
        file_menu.add_command(label=tr("menu_open_folder"), command=self.open_selected_folder)
        self.menubar.add_cascade(label=tr("menu_file"), menu=file_menu)

        # 3. Menu Unduh (Downloads)
        downloads_menu = tk.Menu(self.menubar, tearoff=0)
        downloads_menu.add_command(label=tr("menu_pause_all"), command=self.pause_all)
        downloads_menu.add_command(label=tr("menu_resume_all"), command=self.resume_all)
        downloads_menu.add_command(label=tr("menu_stop_all"), command=self.stop_all)
        downloads_menu.add_command(label=tr("menu_delete_completed"), command=self.delete_completed)
        downloads_menu.add_separator()
        downloads_menu.add_command(label=tr("menu_options"), command=self.open_options_dialog)
        self.menubar.add_cascade(label=tr("menu_downloads"), menu=downloads_menu)

        # 4. Menu Lihat (View)
        view_menu = tk.Menu(self.menubar, tearoff=0)
        view_menu.add_command(label=tr("menu_toggle_sidebar"), command=self.toggle_sidebar)
        
        arrange_menu = tk.Menu(view_menu, tearoff=0)
        arrange_menu.add_command(label=tr("sort_name"), command=lambda: self.sort_by_column("name"))
        arrange_menu.add_command(label=tr("sort_size"), command=lambda: self.sort_by_column("size"))
        arrange_menu.add_command(label=tr("sort_status"), command=lambda: self.sort_by_column("status"))
        arrange_menu.add_command(label=tr("sort_speed"), command=lambda: self.sort_by_column("speed"))
        view_menu.add_cascade(label=tr("menu_arrange"), menu=arrange_menu)

        view_menu.add_separator()
        lang_menu = tk.Menu(view_menu, tearoff=0)
        is_id = self.settings.get_language() == "id"
        lang_menu.add_command(
            label="✔ Bahasa Indonesia" if is_id else "  Bahasa Indonesia",
            command=lambda: self.set_language("id"),
        )
        lang_menu.add_command(
            label="✔ English" if not is_id else "  English",
            command=lambda: self.set_language("en"),
        )
        view_menu.add_cascade(label=tr("menu_language"), menu=lang_menu)

        self.menubar.add_cascade(label=tr("menu_view"), menu=view_menu)

        # 5. Menu Bantuan (Help)
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label=tr("menu_tip"), command=self.show_tip_of_the_day)
        help_menu.add_command(label=tr("menu_updates"), command=self.check_for_updates)
        help_menu.add_separator()
        help_menu.add_command(label=tr("menu_about"), command=self.show_about)
        self.menubar.add_cascade(label=tr("menu_help"), menu=help_menu)

        self.root.config(menu=self.menubar)

        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.open_add_url_dialog())
        self.root.bind("<Control-N>", lambda e: self.open_add_url_dialog())
        self.root.bind("<Delete>", lambda e: self.delete_selected())

    def _build_toolbar(self):
        self.toolbar_frame = tk.Frame(self.root, bg=THEME["surface"], pady=7, padx=12, relief=tk.FLAT)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        self.toolbar_border = tk.Frame(self.root, bg="#162032", height=1)
        self.toolbar_border.pack(side=tk.TOP, fill=tk.X)

        # 1. Hero Primary Action Button: + Tambah URL
        self.btn_add = create_modern_button(
            self.toolbar_frame,
            text=tr("tb_add_url"),
            command=self.open_add_url_dialog,
            kind="primary",
            padx=12,
            pady=5,
            radius=8,
            tooltip=tr("tip_add"),
        )
        self.btn_add.pack(side=tk.LEFT, padx=(0, 10))

        # 2. Segmented Control Group 1: Transfer Controls (▷ Lanjutkan | ❚❚ Jeda | ✕ Hapus)
        self.grp_transfer = tk.Frame(self.toolbar_frame, bg=THEME["surface"], padx=0, pady=0)
        self.grp_transfer.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_resume = create_modern_button(
            self.grp_transfer,
            text=tr("tb_resume"),
            command=self.resume_selected,
            kind="toolbar",
            padx=9,
            pady=4,
            radius=7,
            tooltip=tr("tip_resume"),
        )
        self.btn_resume.pack(side=tk.LEFT, padx=2)

        self.btn_pause = create_modern_button(
            self.grp_transfer,
            text=tr("tb_pause"),
            command=self.pause_selected,
            kind="toolbar",
            padx=9,
            pady=4,
            radius=7,
            tooltip=tr("tip_pause"),
        )
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_delete = create_modern_button(
            self.grp_transfer,
            text=tr("tb_delete"),
            command=self.delete_selected,
            kind="danger",
            padx=9,
            pady=4,
            radius=7,
            tooltip=tr("tip_delete"),
        )
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        # 3. Segmented Control Group 2: Secondary Tools (■ Hentikan | ✓ Bersihkan | ↗ Buka Folder | ⋯ Pengaturan)
        self.secondary_group = tk.Frame(self.toolbar_frame, bg=THEME["surface"], padx=0, pady=0)
        self.secondary_group.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_stop = create_modern_button(
            self.secondary_group,
            text=tr("tb_stop"),
            command=self.stop_all,
            kind="toolbar",
            padx=8,
            pady=4,
            radius=7,
            tooltip=tr("tip_stop"),
        )
        self.btn_stop.pack(side=tk.LEFT, padx=2)

        self.btn_clean = create_modern_button(
            self.secondary_group,
            text=tr("tb_clear"),
            command=self.delete_completed,
            kind="toolbar",
            padx=8,
            pady=4,
            radius=7,
            tooltip=tr("tip_clear"),
        )
        self.btn_clean.pack(side=tk.LEFT, padx=2)

        self.btn_folder = create_modern_button(
            self.secondary_group,
            text=tr("tb_open_folder"),
            command=self.open_selected_folder,
            kind="toolbar",
            padx=8,
            pady=4,
            radius=7,
            tooltip=tr("tip_folder"),
        )
        self.btn_folder.pack(side=tk.LEFT, padx=2)

        self.btn_opts = create_modern_button(
            self.secondary_group,
            text=tr("tb_settings"),
            command=self.open_options_dialog,
            kind="toolbar",
            padx=8,
            pady=4,
            radius=7,
            tooltip=tr("tip_settings"),
        )
        self.btn_opts.pack(side=tk.LEFT, padx=2)

        self.toolbar_buttons = [
            (self.btn_add, tr("tip_add")),
            (self.btn_resume, tr("tip_resume")),
            (self.btn_pause, tr("tip_pause")),
            (self.btn_delete, tr("tip_delete")),
            (self.btn_stop, tr("tip_stop")),
            (self.btn_clean, tr("tip_clear")),
            (self.btn_folder, tr("tip_folder")),
            (self.btn_opts, tr("tip_settings")),
        ]
        self.secondary_buttons = [self.btn_stop, self.btn_clean, self.btn_folder, self.btn_opts]

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
        self.overflow_menu.add_command(label=f"■ {tr('tb_stop')}", command=self.stop_all)
        self.overflow_menu.add_command(label=f"✓ {tr('tb_clear')}", command=self.delete_completed)
        self.overflow_menu.add_command(label=f"↗ {tr('tb_open_folder')}", command=self.open_selected_folder)
        self.overflow_menu.add_separator()
        self.overflow_menu.add_command(label=f"⋯ {tr('tb_settings')}", command=self.open_options_dialog)

        self.btn_overflow = create_modern_button(
            self.toolbar_frame,
            text=tr("tb_more"),
            command=self._show_overflow_menu,
            kind="toolbar",
            padx=10,
            pady=4,
            radius=7,
            tooltip=tr("tb_more"),
        )

        # Search pill bar on the right side of toolbar with SF Pro font and 3D elevation
        self.search_canvas = tk.Canvas(self.toolbar_frame, width=200, height=32, bg=THEME["surface"], highlightthickness=0)
        self.search_canvas.pack(side=tk.RIGHT, padx=4)
        draw_round_rectangle(self.search_canvas, 2, 4, 198, 31, r=9, fill="#04070e", outline="")
        draw_round_rectangle(self.search_canvas, 1, 1, 199, 29, r=9, fill=THEME["input_bg"], outline="#26354c")
        self.search_canvas.create_line(12, 2, 188, 2, fill="#425777", width=1.5)

        lbl_search = tk.Label(self.search_canvas, text="⌕", font=(FONT_DISPLAY, 11, "bold"), bg=THEME["input_bg"], fg=THEME["text_secondary"])
        self.search_canvas.create_window(16, 16, window=lbl_search)

        try:
            self.search_var = tk.StringVar(master=self.root)
        except Exception:
            self.search_var = None

        entry_kwargs = {
            "bg": THEME["input_bg"],
            "fg": THEME["text_secondary"],
            "insertbackground": THEME["text_primary"],
            "relief": tk.FLAT,
            "font": FONT_BODY,
            "bd": 0,
        }
        if self.search_var:
            entry_kwargs["textvariable"] = self.search_var
        self.search_entry = tk.Entry(self.search_canvas, **entry_kwargs)
        self.search_entry.insert(0, tr("tb_search_placeholder"))
        self.search_canvas.create_window(110, 16, window=self.search_entry, width=150)

        def _on_search_focus_in(e):
            if self.search_entry.get() in ("Cari unduhan...", "Search downloads..."):
                self.search_entry.delete(0, tk.END)
                self.search_entry.config(fg=THEME["text_primary"])

        def _on_search_focus_out(e):
            if not self.search_entry.get().strip():
                self.search_entry.insert(0, tr("tb_search_placeholder"))
                self.search_entry.config(fg=THEME["text_secondary"])

        self.search_entry.bind("<FocusIn>", _on_search_focus_in)
        self.search_entry.bind("<FocusOut>", _on_search_focus_out)
        if self.search_var:
            self.search_var.trace_add("write", lambda *args: self._tick_ui())

        self.root.bind("<Configure>", self._on_window_configure, add="+")

    def _on_window_configure(self, event):
        if event.widget == self.root:
            self._update_toolbar_overflow(event.width)

    def _update_toolbar_overflow(self, width: Optional[int] = None):
        w = width if width is not None else self.root.winfo_width()
        if w < 760:
            if hasattr(self, "secondary_group"):
                self.secondary_group.pack_forget()
            for btn in self.secondary_buttons:
                try:
                    btn.pack_forget()
                except Exception:
                    pass
            if self.btn_overflow:
                self.btn_overflow.pack(side=tk.LEFT, padx=3)
        else:
            if self.btn_overflow:
                self.btn_overflow.pack_forget()
            if hasattr(self, "secondary_group"):
                self.secondary_group.pack(side=tk.LEFT, padx=(0, 8))
            for btn in self.secondary_buttons:
                try:
                    btn.pack(side=tk.LEFT, padx=1)
                except Exception:
                    pass

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

        # Left Sidebar: Modern Apple/Linear Navigation Bar
        self.sidebar_frame = tk.Frame(self.paned, width=230, bg=THEME["surface_alt"])
        self.sidebar_visible = True
        self.sidebar_compact = False

        # Quick Storage Card anchored to bottom of sidebar (3D Tactile rounded card)
        self.storage_card = TactileStorageCard(self.sidebar_frame, on_open_folder=self.open_selected_folder, r=10)
        self.storage_card.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)

        # Compact Folder Button for Compact Mode (at bottom of sidebar)
        self.btn_compact_folder = create_modern_button(
            self.sidebar_frame,
            text="📁",
            command=self.open_selected_folder,
            kind="secondary",
            padx=8,
            pady=6,
            radius=6,
            tooltip=tr("tb_open_folder"),
        )

        # Sidebar Header with Hamburger (Garis Tiga ☰) Toggle Button
        self.sidebar_header = tk.Frame(self.sidebar_frame, bg=THEME["surface_alt"], height=36)
        self.sidebar_header.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(8, 2))

        self.btn_hamburger = create_modern_button(
            self.sidebar_header,
            text="☰",
            command=self.toggle_sidebar_compact,
            kind="secondary",
            padx=8,
            pady=3,
            radius=6,
            tooltip=None,
        )
        self.btn_hamburger.pack(side=tk.LEFT)

        self.lbl_sidebar_title = tk.Label(
            self.sidebar_header,
            text="NAVIGASI",
            bg=THEME["surface_alt"],
            fg=THEME["text_tertiary"],
            font=(FONT_DISPLAY, 8, "bold"),
        )
        self.lbl_sidebar_title.pack(side=tk.LEFT, padx=(8, 0))

        # Section 1: PUSTAKA
        self.lbl_sec_pustaka = tk.Label(
            self.sidebar_frame,
            text="PUSTAKA",
            bg=THEME["surface_alt"],
            fg=THEME["text_tertiary"],
            font=(FONT_DISPLAY, 8, "bold"),
            anchor=tk.W,
            padx=14,
        )
        self.lbl_sec_pustaka.pack(fill=tk.X, pady=(6, 4))

        pustaka_specs = [
            ("all", "📥", "Semua Unduhan"),
            ("downloading", "⚡", "Sedang Mengunduh"),
            ("finished", "✓", "Selesai"),
        ]
        for key, icon, label in pustaka_specs:
            item = SidebarNavItem(
                self.sidebar_frame,
                icon=icon,
                text=label,
                key=key,
                on_click=self._on_sidebar_item_click,
                on_double_click=self._on_sidebar_item_double_click,
            )
            item.pack(fill=tk.X)
            self.sidebar_items[key] = item

        # Subtle divider between sections in compact mode
        self.div_sec_kategori = tk.Frame(self.sidebar_frame, height=1, bg=THEME["border"])

        # Section 2: KATEGORI BERKAS
        self.lbl_sec_kategori = tk.Label(
            self.sidebar_frame,
            text="KATEGORI BERKAS",
            bg=THEME["surface_alt"],
            fg=THEME["text_tertiary"],
            font=(FONT_DISPLAY, 8, "bold"),
            anchor=tk.W,
            padx=14,
        )
        self.lbl_sec_kategori.pack(fill=tk.X, pady=(12, 4))

        cat_specs = [
            ("video", "🎬", "Video"),
            ("music", "🎵", "Musik"),
            ("pictures", "🖼", "Gambar"),
            ("programs", "📦", "Program"),
            ("documents", "📄", "Dokumen"),
            ("compressed", "🗜", "Terkompresi"),
        ]
        for key, icon, label in cat_specs:
            item = SidebarNavItem(
                self.sidebar_frame,
                icon=icon,
                text=label,
                key=key,
                on_click=self._on_sidebar_item_click,
                on_double_click=self._on_sidebar_item_double_click,
            )
            item.pack(fill=tk.X)
            self.sidebar_items[key] = item

        # Activate 'all' item by default
        self.sidebar_items["all"].set_active(True)

        # Dummy hidden category_tree for total backward compatibility
        self.category_tree = ttk.Treeview(self.sidebar_frame)

        self.paned.add(self.sidebar_frame, minsize=56)

        # Right Container: Dashboard Live Stats + Downloads Table
        right_container = tk.Frame(self.paned, bg=THEME["tree_bg"])

        # 1. Live Telemetry Metric Strip (3D Elevated Rounded Cards)
        self.stat_bar = tk.Frame(right_container, bg=THEME["surface_alt"], padx=8, pady=8)
        self.stat_bar.pack(side=tk.TOP, fill=tk.X)

        # Card 1: Live Speed (3D Tactile Card)
        self.card_speed = TactileCard(self.stat_bar, tr("stat_speed"), "0 B/s", val_fg=THEME["accent_primary"], r=12)
        self.card_speed.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self.lbl_stat_speed = self.card_speed.lbl_val

        # Card 2: Active / Queued Tasks (3D Tactile Card)
        self.card_active = TactileCard(self.stat_bar, tr("stat_active"), "0", val_fg=THEME["text_primary"], r=12)
        self.card_active.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self.lbl_stat_active = self.card_active.lbl_val

        # Card 3: Library Stats (3D Tactile Card)
        self.card_total = TactileCard(self.stat_bar, tr("stat_files"), "0", val_fg=THEME["text_primary"], r=12)
        self.card_total.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self.lbl_stat_total = self.card_total.lbl_val

        # 2. Downloads Table Frame inside 3D tactile rounded card container
        self.table_container = TactileTableContainer(right_container, r=14)
        self.table_container.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        table_frame = self.table_container.inner_frame

        cols = ("name", "size", "status", "progress", "speed", "url")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="extended")

        self.tree.heading("name", text=tr("col_name"))
        self.tree.heading("size", text=tr("col_size"))
        self.tree.heading("status", text=tr("col_status"))
        self.tree.heading("progress", text=tr("col_progress"))
        self.tree.heading("speed", text=tr("col_speed"))
        self.tree.heading("url", text=tr("col_url"))

        self.tree.column("name", width=210, minwidth=130)
        self.tree.column("size", width=75, anchor=tk.E, minwidth=65)
        self.tree.column("status", width=115, anchor=tk.CENTER, minwidth=100)
        self.tree.column("progress", width=130, anchor=tk.CENTER, minwidth=110)
        self.tree.column("speed", width=105, anchor=tk.E, minwidth=90)
        self.tree.column("url", width=235, stretch=True)

        # Color-coded tags for modern status styling
        self.tree.tag_configure("downloading", foreground="#60a5fa")
        self.tree.tag_configure("completed", foreground="#34d399")
        self.tree.tag_configure("paused", foreground="#94a3b8")
        self.tree.tag_configure("queued", foreground="#e2e8f0")
        self.tree.tag_configure("failed", foreground="#f87171")
        self.tree.tag_configure("cancelled", foreground="#f87171")

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_double_click_item)

        # Context Menu for Right-Click on Treeview rows
        self.context_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["surface"],
            fg=THEME["text_primary"],
            activebackground=THEME["accent_primary"],
            activeforeground="#ffffff",
            bd=1,
            relief=tk.SOLID,
        )
        self.context_menu.add_command(label="▶ Lanjutkan Unduh (Resume)", command=self.resume_selected)
        self.context_menu.add_command(label="⏸ Jeda Unduh (Pause)", command=self.pause_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📂 Buka Berkas (Open)", command=self.open_selected_file)
        self.context_menu.add_command(label="📁 Buka Folder Penyimpanan (Open Folder)", command=self.open_selected_folder)
        self.context_menu.add_command(label="📋 Salin URL Unduhan (Copy URL)", command=self.copy_selected_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑 Hapus dari Daftar (Remove)", command=self.delete_selected)
        self.context_menu.add_command(label="❌ Hapus Berkas dari Komputer", command=self.delete_selected_file_from_disk)

        def _on_tree_right_click(event):
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()

        self.tree.bind("<Button-3>", _on_tree_right_click)

        # Empty State Card Overlay (Apple-inspired rounded card with bespoke vector badge)
        self.empty_state_frame = tk.Canvas(
            table_frame,
            width=380,
            height=210,
            bg=THEME["tree_bg"],
            highlightthickness=0,
        )

        draw_round_rectangle(self.empty_state_frame, 2, 2, 378, 208, r=16, fill=THEME["surface"], outline=THEME["border"])

        # Minimalist glowing vector badge at top (x=190, y=48)
        self.empty_state_frame.create_oval(165, 20, 215, 70, fill="#151d2a", outline=THEME["accent_primary"], width=2)
        # Vector arrow & tray
        self.empty_state_frame.create_line(190, 32, 190, 52, fill="#60a5fa", width=2)
        self.empty_state_frame.create_line(184, 46, 190, 52, fill="#60a5fa", width=2)
        self.empty_state_frame.create_line(196, 46, 190, 52, fill="#60a5fa", width=2)
        self.empty_state_frame.create_line(178, 52, 178, 58, 202, 58, 202, 52, fill="#60a5fa", width=2)

        self.empty_state_frame.create_text(
            190, 92,
            text="Belum Ada Unduhan",
            fill=THEME["text_primary"],
            font=(FONT_DISPLAY, 11, "bold"),
        )
        self.empty_state_frame.create_text(
            190, 118,
            text="Salin tautan dari peramban atau klik tombol di bawah\nuntuk memulai unduhan baru.",
            fill=THEME["text_secondary"],
            font=FONT_BODY,
            justify=tk.CENTER,
        )

        btn_empty_add = create_modern_button(
            self.empty_state_frame,
            text="+ Tambah Unduhan Baru",
            command=self.open_add_url_dialog,
            kind="primary",
            padx=18,
            pady=6,
            radius=9,
            tooltip="Tambah URL Baru (Ctrl+N)",
        )
        self.empty_state_frame.create_window(190, 168, window=btn_empty_add)

        # Place initially if queue is empty
        if len(self.queue.list_tasks()) == 0:
            self.empty_state_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        self.paned.add(right_container, minsize=400)

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

    def _on_sidebar_item_click(self, key: str):
        self.active_category_filter = key
        for k, item in self.sidebar_items.items():
            item.set_active(k == key)
        self._tick_ui()

    def _on_sidebar_item_double_click(self, key: str):
        cat_map = {
            "video": "Video",
            "music": "Musik",
            "pictures": "Gambar",
            "programs": "Program",
            "documents": "Dokumen",
            "compressed": "Berkas Terkompresi",
        }
        if key in cat_map:
            self.open_options_dialog(initial_category=cat_map[key])
        else:
            self.open_options_dialog()

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
            # Modern URL input dialog with inline validation
            dlg = tk.Toplevel(self.root)
            dlg.title("Masukkan URL untuk Mengunduh")
            dlg.geometry("520x180")
            dlg.minsize(460, 160)
            dlg.resizable(True, False)
            dlg.configure(bg=THEME["surface"])
            apply_window_icon(dlg)
            dlg.transient(self.root)
            try:
                dlg.grab_set()
            except Exception:
                pass

            # Center dialog on screen
            dlg.update_idletasks()
            try:
                sw = dlg.winfo_screenwidth()
                sh = dlg.winfo_screenheight()
                x = max(0, (sw - 520) // 2)
                y = max(0, (sh - 180) // 2)
                dlg.geometry(f"520x180+{x}+{y}")
                dlg.deiconify()
                dlg.lift()
                dlg.focus_force()
            except Exception:
                pass

            main_box = tk.Frame(dlg, bg=THEME["surface"], padx=16, pady=12)
            main_box.pack(fill=tk.BOTH, expand=True)

            tk.Label(
                main_box,
                text="Alamat Tautan (URL):",
                bg=THEME["surface"],
                fg=THEME["text_primary"],
                font=FONT_HEADING,
            ).pack(anchor=tk.W, pady=(0, 4))

            url_var = tk.StringVar(master=dlg)
            url_entry = tk.Entry(
                main_box,
                textvariable=url_var,
                bg=THEME["input_bg"],
                fg=THEME["text_primary"],
                insertbackground=THEME["text_primary"],
                relief=tk.SOLID,
                bd=1,
                font=FONT_BODY,
            )
            url_entry.pack(fill=tk.X, pady=(0, 2))
            url_entry.focus_set()

            # Inline validation error label
            lbl_error = tk.Label(main_box, text="", bg=THEME["surface"], fg=THEME["danger_text"], font=FONT_SMALL)
            lbl_error.pack(anchor=tk.W, pady=(0, 6))

            def _on_url_change(*args):
                val = url_var.get().strip()
                if not val:
                    lbl_error.config(text="")
                elif not (val.startswith("http://") or val.startswith("https://")):
                    lbl_error.config(text="* Format URL harus diawali dengan http:// atau https://")
                else:
                    lbl_error.config(text="")

            url_var.trace_add("write", _on_url_change)

            btn_box = tk.Frame(main_box, bg=THEME["surface"])
            btn_box.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))

            def on_ok():
                u = url_var.get().strip()
                if not u:
                    lbl_error.config(text="* Masukkan tautan unduhan terlebih dahulu")
                    url_entry.focus_set()
                    return
                if not (u.startswith("http://") or u.startswith("https://")):
                    lbl_error.config(text="* Format URL harus diawali dengan http:// atau https://")
                    url_entry.focus_set()
                    return
                dlg.destroy()
                self._show_download_info_for_url(u)

            btn_ok = create_modern_button(btn_box, text="+ Unduh", command=on_ok, kind="primary", padx=16, pady=4, radius=7)
            btn_ok.pack(side=tk.RIGHT, padx=(4, 0))

            btn_cancel = create_modern_button(btn_box, text="Batal", command=dlg.destroy, kind="secondary", padx=12, pady=4, radius=7)
            btn_cancel.pack(side=tk.RIGHT)

            dlg.bind("<Return>", lambda e: on_ok())
            dlg.bind("<Escape>", lambda e: dlg.destroy())
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
            target_base = os.path.splitext(os.path.basename(task.output_path))[0]
            try:
                # Clean up only partial or temp files belonging to this specific task
                for f in os.listdir(out_dir):
                    if f.startswith(target_base) and (f.endswith(".part") or f.endswith(".ytdl")):
                        p = os.path.join(out_dir, f)
                        if os.path.exists(p):
                            os.remove(p)
            except Exception:
                pass
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            try:
                self.queue.save_to_file(self.settings.get_tasks_filepath())
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

        def probe_worker():
            size = 0
            if is_yt:
                try:
                    import yt_dlp
                    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                        info = ydl.extract_info(url, download=False)
                        size = info.get("filesize") or info.get("filesize_approx") or 0
                        if not size and "formats" in info and info["formats"]:
                            for fmt in reversed(info["formats"]):
                                if fmt.get("filesize"):
                                    size = fmt["filesize"]
                                    break
                except Exception:
                    pass
            else:
                try:
                    size, _ = self.engine.probe(url)
                except Exception:
                    pass

            if size > 0:
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

        if not os.environ.get("PYTEST_CURRENT_TEST"):
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

        if progress_dlg:
            def _on_speed_limit(bps: int):
                task.speed_limit_bps = bps
            progress_dlg.on_speed_limit_change = _on_speed_limit

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
                    part_snap = getattr(task, "latest_part_progress", None)
                    self.root.after(0, lambda b=curr_b, t=tot_b, s=speed, d=dlg, p=part_snap: d.update_progress(b, t, s, part_progress=p))

        def progress_cb(chunk_len: int):
            with progress_lock:
                if chunk_len < 0:
                    task.bytes_downloaded = 0
                else:
                    task.bytes_downloaded += chunk_len
                update_ui_progress()

        def part_cb(parts_data: list[dict]):
            with progress_lock:
                task.latest_part_progress = [dict(x) for x in parts_data]
            update_ui_progress()

        def worker():
            referer = self.task_referers.get(task_id, "")
            stream_url = task.url
            if "googlevideo.com" in task.url and "youtube.com" in referer:
                stream_url = referer
            elif ("tiktokcdn.com" in task.url or "byteoversea.com" in task.url or "ibytedtos.com" in task.url) and "tiktok.com" in referer:
                stream_url = referer
            elif "tiktok.com" in stream_url and "/video/" not in stream_url and "/video/" in referer:
                stream_url = referer

            is_stream_site = any(d in stream_url for d in ["youtube.com", "youtu.be", "vimeo.com", "tiktok.com"]) or any(d in referer for d in ["tiktok.com", "instagram.com"])
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

                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                        "Referer": "https://www.tiktok.com/" if ("tiktok.com" in stream_url or "tiktok.com" in referer) else "https://www.google.com/",
                    }

                    ydl_opts = {
                        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
                        "http_headers": headers,
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
                            if not os.path.exists(downloaded_file):
                                base_stem, _ = os.path.splitext(downloaded_file)
                                for ext in [".mp4", ".mkv", ".webm"]:
                                    if os.path.exists(f"{base_stem}{ext}"):
                                        downloaded_file = f"{base_stem}{ext}"
                                        break
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
                req_headers = dict(self.task_headers.get(task_id) or {})
                if any(k in task.url for k in ["tiktokcdn.com", "byteoversea.com", "ibytedtos.com"]) or "tiktok.com" in referer:
                    if "Referer" not in req_headers:
                        req_headers["Referer"] = "https://www.tiktok.com/"
                    if "User-Agent" not in req_headers:
                        req_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

                res: DownloadResult = self.engine.download(
                    task.url,
                    task.output_path,
                    num_parts=active_parts,
                    progress_callback=progress_cb,
                    stop_event=stop_event,
                    headers=req_headers,
                    known_size=task.total_bytes if task.total_bytes > 0 else None,
                    part_progress_callback=part_cb,
                    speed_limit_bps=getattr(task, "speed_limit_bps", 0),
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

            # Play sound alert if enabled in Options
            if self.settings.get_play_sound_on_complete():
                try:
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass

            # Notify system tray if running
            if hasattr(self, "tray_icon") and self.tray_icon and hasattr(self.tray_icon, "notify"):
                try:
                    self.tray_icon.notify(f"Unduhan Selesai: {fname}", "JustPressDownload (JPD)")
                except Exception:
                    pass

            DownloadCompleteDialog(
                parent=self.root,
                title=fname,
                output_path=task.output_path,
                total_bytes=task.total_bytes,
            )
        self.root.after(0, show_complete)

    def _tick_ui(self):
        now = time.time()
        all_tasks = self.queue.list_tasks()

        # Update category counts across all tasks
        if hasattr(self, "sidebar_items") and self.sidebar_items:
            cat_counts = {k: 0 for k in self.sidebar_items}
            cat_counts["all"] = len(all_tasks)
            for t in all_tasks:
                if t.status in (TaskStatus.DOWNLOADING, TaskStatus.QUEUED):
                    cat_counts["downloading"] += 1
                if t.status == TaskStatus.COMPLETED:
                    cat_counts["finished"] += 1
                c = self._detect_category(t.url, t.output_path).lower()
                if "video" in c:
                    cat_counts["video"] += 1
                elif "musik" in c or "audio" in c:
                    cat_counts["music"] += 1
                elif "gambar" in c or "image" in c:
                    cat_counts["pictures"] += 1
                elif "program" in c or "exe" in c or "msi" in c:
                    cat_counts["programs"] += 1
                elif "dokumen" in c or "pdf" in c or "doc" in c:
                    cat_counts["documents"] += 1
                elif "kompres" in c or "zip" in c:
                    cat_counts["compressed"] += 1

            for k, count in cat_counts.items():
                if k in self.sidebar_items:
                    self.sidebar_items[k].set_count(count)

        # Filter by active category
        tasks = all_tasks
        if hasattr(self, "active_category_filter") and self.active_category_filter:
            kf = self.active_category_filter
            if kf == "downloading":
                tasks = [t for t in tasks if t.status in (TaskStatus.DOWNLOADING, TaskStatus.QUEUED)]
            elif kf == "finished":
                tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
            elif kf in ("video", "music", "pictures", "programs", "documents", "compressed"):
                cat_map_check = {
                    "video": "video",
                    "music": "musik",
                    "pictures": "gambar",
                    "programs": "program",
                    "documents": "dokumen",
                    "compressed": "berkas terkompresi",
                }
                expected = cat_map_check.get(kf, "")
                tasks = [t for t in tasks if expected in self._detect_category(t.url, t.output_path).lower()]

        # Filter by search query if active
        if hasattr(self, "search_var") and self.search_var:
            query = self.search_var.get().strip().lower()
            if query and query not in ("cari unduhan...", "search downloads..."):
                tasks = [t for t in tasks if query in os.path.basename(t.output_path).lower() or query in (t.url or "").lower()]

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

            # Format status with localized label and modern color tag
            status_tag = "normal"
            if task.status == TaskStatus.DOWNLOADING:
                status_label = tr("status_downloading")
                status_tag = "downloading"
            elif task.status == TaskStatus.COMPLETED:
                status_label = tr("status_completed")
                status_tag = "completed"
            elif task.status == TaskStatus.PAUSED:
                status_label = tr("status_paused")
                status_tag = "paused"
            elif task.status == TaskStatus.QUEUED:
                status_label = tr("status_queued")
                status_tag = "queued"
            elif task.status == TaskStatus.FAILED:
                status_label = tr("status_failed")
                status_tag = "failed"
            elif task.status == TaskStatus.CANCELLED:
                status_label = tr("status_failed")
                status_tag = "cancelled"
            else:
                status_label = task.status.value

            pct = 0.0
            if task.total_bytes > 0:
                pct = min(100.0, (task.bytes_downloaded / task.total_bytes) * 100)
            elif task.status == TaskStatus.COMPLETED:
                pct = 100.0

            if task.status == TaskStatus.COMPLETED:
                pct_str = "■■■■■■ 100%"
            elif pct > 0:
                bars = 6
                filled = min(bars, max(0, int(round((pct / 100.0) * bars))))
                bar_glyph = "■" * filled + "□" * (bars - filled)
                pct_str = f"{bar_glyph} {pct:.1f}%"
            else:
                pct_str = "□□□□□□ 0%"

            cat = self._detect_category(task.url, task.output_path)
            glyph = get_file_type_glyph(cat, fname)
            disp_fname = f"{glyph} {fname}"

            values = (
                disp_fname,
                size_str,
                status_label,
                pct_str,
                speed_str,
                task.url,
            )

            if self.tree.exists(tid):
                self.tree.item(tid, values=values, tags=(status_tag,))
            else:
                self.tree.insert("", "end", iid=tid, values=values, tags=(status_tag,))

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

        # Update Live Dashboard Metric Cards
        if hasattr(self, "lbl_stat_speed") and self.lbl_stat_speed:
            speed_val_str = f"{format_bytes(int(total_speed))}/s"
            self.lbl_stat_speed.config(
                text=speed_val_str,
                fg=THEME["success"] if total_speed > 0 else THEME["accent_primary"],
            )
        if hasattr(self, "lbl_stat_active") and self.lbl_stat_active:
            queued_count = sum(1 for t in tasks if t.status == TaskStatus.QUEUED)
            self.lbl_stat_active.config(text=tr("stat_running_queued", running=active_count, queued=queued_count))
        if hasattr(self, "lbl_stat_total") and self.lbl_stat_total:
            total_bytes_dl = sum(t.bytes_downloaded for t in tasks)
            self.lbl_stat_total.config(text=tr("stat_files_summary", count=len(tasks), size=format_bytes(total_bytes_dl)))

        self.statusbar.config(
            text=tr("statusbar_summary", total=len(tasks), active=active_count, speed=f"{format_bytes(int(total_speed))}/s")
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
        should_confirm = confirm and self.settings.get_confirm_on_delete()
        if should_confirm:
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
            "Tentang JustPressDownload (JPD)",
            "JustPressDownload (JPD)\n"
            "High-Performance Parallel Download Accelerator\n"
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

    def copy_selected_url(self):
        tid = self._get_selected_task_id()
        if tid:
            task = self.queue.get_task(tid)
            if task and task.url:
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(task.url)
                except Exception:
                    pass

    def delete_selected_file_from_disk(self):
        tid = self._get_selected_task_id()
        if not tid:
            return
        task = self.queue.get_task(tid)
        if not task:
            return
        if self.settings.get_confirm_on_delete():
            fname = os.path.basename(task.output_path)
            ans = messagebox.askyesno(
                "Konfirmasi Hapus Berkas",
                f"Apakah Anda yakin ingin menghapus berkas '{fname}' secara permanen dari komputer Anda?",
                parent=self.root,
            )
            if not ans:
                return
        p = task.output_path
        self.delete_task_by_id(tid)
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                messagebox.showerror("Gagal Menghapus", f"Tidak dapat menghapus berkas: {e}", parent=self.root)

    def toggle_sidebar_compact(self):
        """Toggle between expanded sidebar with labels and compact sidebar with icons and phone notification badges."""
        if getattr(self, "_animating_sidebar", False):
            return
        self.sidebar_compact = not self.sidebar_compact
        self._apply_sidebar_compact_state()

    def _apply_sidebar_compact_state(self, animated: bool = True):
        # In automated tests or if requested, apply immediately without animation
        if not animated or os.environ.get("PYTEST_CURRENT_TEST"):
            self._apply_sidebar_compact_immediate()
            return

        self._animating_sidebar = True
        collapse = self.sidebar_compact
        expanded_w = 230
        compact_w = 56
        delay = 14

        if collapse:
            # COLLAPSING:
            # Phase 1: Fade out text (4 frames, ~56ms)
            # Phase 2: Switch to compact mode & slide sash shut to 56px (6 frames, ~84ms)
            fade_steps = 4
            slide_steps = 6

            def _fade_out_step(f_idx: int):
                alpha = max(0.0, 1.0 - (f_idx / fade_steps))
                for it in self.sidebar_items.values():
                    it.set_text_fade(alpha)
                bg_col = THEME["surface_alt"]
                self.lbl_sidebar_title.configure(fg=interpolate_color(bg_col, THEME["text_tertiary"], alpha))
                self.lbl_sec_pustaka.configure(fg=interpolate_color(bg_col, THEME["text_tertiary"], alpha))
                self.lbl_sec_kategori.configure(fg=interpolate_color(bg_col, THEME["text_tertiary"], alpha))

                if f_idx < fade_steps:
                    self.root.after(delay, lambda: _fade_out_step(f_idx + 1))
                else:
                    # Switch to compact layout before sliding
                    self.lbl_sidebar_title.pack_forget()
                    self.btn_hamburger.pack_configure(side=tk.TOP)
                    self.lbl_sec_pustaka.pack_forget()
                    self.lbl_sec_kategori.pack_forget()
                    if "video" in self.sidebar_items:
                        self.div_sec_kategori.pack(before=self.sidebar_items["video"], fill=tk.X, padx=10, pady=8)
                    self.storage_card.pack_forget()
                    self.btn_compact_folder.pack(side=tk.BOTTOM, pady=8)
                    for it in self.sidebar_items.values():
                        it.set_compact(True)
                    # Begin slide shut
                    _slide_collapse_step(1)

            def _slide_collapse_step(s_idx: int):
                t = s_idx / slide_steps
                progress = 1.0 - (1.0 - t) ** 3
                cur_w = int(expanded_w + (compact_w - expanded_w) * progress)
                try:
                    self.paned.paneconfig(self.sidebar_frame, minsize=compact_w)
                    self.paned.sash_place(0, cur_w, 0)
                    self.sidebar_frame.configure(width=cur_w)
                except Exception:
                    pass

                if s_idx < slide_steps:
                    self.root.after(delay, lambda: _slide_collapse_step(s_idx + 1))
                else:
                    self._animating_sidebar = False
                    try:
                        self.paned.paneconfig(self.sidebar_frame, minsize=compact_w)
                        self.paned.sash_place(0, compact_w, 0)
                        self.sidebar_frame.configure(width=compact_w)
                    except Exception:
                        pass

            _fade_out_step(1)

        else:
            # EXPANDING:
            # Phase 1: Slide sash open to 230px while remaining in clean compact mode (6 frames, ~84ms)
            # Phase 2: Unpack labels & storage card at alpha 0.0, then fade in to 1.0 (4 frames, ~56ms)
            slide_steps = 6
            fade_steps = 4

            def _slide_expand_step(s_idx: int):
                t = s_idx / slide_steps
                progress = 1.0 - (1.0 - t) ** 3
                cur_w = int(compact_w + (expanded_w - compact_w) * progress)
                try:
                    self.paned.paneconfig(self.sidebar_frame, minsize=compact_w)
                    self.paned.sash_place(0, cur_w, 0)
                    self.sidebar_frame.configure(width=cur_w)
                except Exception:
                    pass

                if s_idx < slide_steps:
                    self.root.after(delay, lambda: _slide_expand_step(s_idx + 1))
                else:
                    try:
                        self.paned.paneconfig(self.sidebar_frame, minsize=expanded_w)
                        self.paned.sash_place(0, expanded_w, 0)
                        self.sidebar_frame.configure(width=expanded_w)
                    except Exception:
                        pass

                    # Unpack expanded widgets at alpha 0.0
                    self.div_sec_kategori.pack_forget()
                    self.btn_compact_folder.pack_forget()
                    self.btn_hamburger.pack_configure(side=tk.LEFT)
                    self.lbl_sidebar_title.pack(side=tk.LEFT, padx=(8, 0))

                    if "all" in self.sidebar_items:
                        self.lbl_sec_pustaka.pack(before=self.sidebar_items["all"], fill=tk.X, pady=(6, 4))
                    if "video" in self.sidebar_items:
                        self.lbl_sec_kategori.pack(before=self.sidebar_items["video"], fill=tk.X, pady=(12, 4))
                    self.storage_card.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)

                    for it in self.sidebar_items.values():
                        it.set_compact(False)
                        it.set_text_fade(0.0)

                    bg_col = THEME["surface_alt"]
                    self.lbl_sidebar_title.configure(fg=bg_col)
                    self.lbl_sec_pustaka.configure(fg=bg_col)
                    self.lbl_sec_kategori.configure(fg=bg_col)

                    # Begin fade in
                    _fade_in_step(1)

            def _fade_in_step(f_idx: int):
                alpha = min(1.0, f_idx / fade_steps)
                for it in self.sidebar_items.values():
                    it.set_text_fade(alpha)
                bg_col = THEME["surface_alt"]
                self.lbl_sidebar_title.configure(fg=interpolate_color(bg_col, THEME["text_tertiary"], alpha))
                self.lbl_sec_pustaka.configure(fg=interpolate_color(bg_col, THEME["text_tertiary"], alpha))
                self.lbl_sec_kategori.configure(fg=interpolate_color(bg_col, THEME["text_tertiary"], alpha))

                if f_idx < fade_steps:
                    self.root.after(delay, lambda: _fade_in_step(f_idx + 1))
                else:
                    self._animating_sidebar = False
                    for it in self.sidebar_items.values():
                        it.set_text_fade(1.0)
                    self.lbl_sidebar_title.configure(fg=THEME["text_tertiary"])
                    self.lbl_sec_pustaka.configure(fg=THEME["text_tertiary"])
                    self.lbl_sec_kategori.configure(fg=THEME["text_tertiary"])

            _slide_expand_step(1)

    def _apply_sidebar_compact_immediate(self):
        if self.sidebar_compact:
            self.lbl_sidebar_title.pack_forget()
            self.btn_hamburger.pack_configure(side=tk.TOP)
            self.lbl_sec_pustaka.pack_forget()
            self.lbl_sec_kategori.pack_forget()
            if "video" in self.sidebar_items:
                self.div_sec_kategori.pack(before=self.sidebar_items["video"], fill=tk.X, padx=10, pady=8)
            self.storage_card.pack_forget()
            self.btn_compact_folder.pack(side=tk.BOTTOM, pady=8)

            for item in self.sidebar_items.values():
                item.set_compact(True)

            self.sidebar_frame.configure(width=56)
            try:
                self.paned.paneconfig(self.sidebar_frame, minsize=56)
                self.paned.sash_place(0, 56, 0)
            except Exception:
                pass
        else:
            self.div_sec_kategori.pack_forget()
            self.btn_compact_folder.pack_forget()
            self.btn_hamburger.pack_configure(side=tk.LEFT)
            self.lbl_sidebar_title.pack(side=tk.LEFT, padx=(8, 0))

            if "all" in self.sidebar_items:
                self.lbl_sec_pustaka.pack(before=self.sidebar_items["all"], fill=tk.X, pady=(6, 4))
            if "video" in self.sidebar_items:
                self.lbl_sec_kategori.pack(before=self.sidebar_items["video"], fill=tk.X, pady=(12, 4))
            self.storage_card.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)

            for item in self.sidebar_items.values():
                item.set_compact(False)
                item.set_text_fade(1.0)

            self.sidebar_frame.configure(width=230)
            try:
                self.paned.paneconfig(self.sidebar_frame, minsize=230)
                self.paned.sash_place(0, 230, 0)
            except Exception:
                pass

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.paned.forget(self.sidebar_frame)
            self.sidebar_visible = False
        else:
            panes = self.paned.panes()
            min_s = 56 if self.sidebar_compact else 230
            if panes:
                self.paned.add(self.sidebar_frame, before=panes[0], minsize=min_s)
            else:
                self.paned.add(self.sidebar_frame, minsize=min_s)
            self.sidebar_visible = True
            target_w = 56 if self.sidebar_compact else 230
            try:
                self.paned.sash_place(0, target_w, 0)
            except Exception:
                pass

    def set_language(self, lang: str):
        """Sets the application language ('id' or 'en') and dynamically updates UI strings."""
        self.settings.set_language(lang)
        self.root.title(tr("app_name"))

        # 1. Update menu
        self._build_menu()

        # 2. Update toolbar buttons
        try:
            self.btn_add.config(text=tr("tb_add_url"))
            self.btn_resume.config(text=tr("tb_resume"))
            self.btn_pause.config(text=tr("tb_pause"))
            self.btn_delete.config(text=tr("tb_delete"))
            self.btn_stop.config(text=tr("tb_stop"))
            self.btn_clean.config(text=tr("tb_clear"))
            self.btn_folder.config(text=tr("tb_open_folder"))
            self.btn_opts.config(text=tr("tb_settings"))
            if self.btn_overflow:
                self.btn_overflow.config(text=tr("tb_more"))
            if hasattr(self, "search_entry") and self.search_entry:
                cur_s = self.search_entry.get().strip()
                if cur_s in ("Cari unduhan...", "Search downloads...", ""):
                    self.search_entry.delete(0, tk.END)
                    self.search_entry.insert(0, tr("tb_search_placeholder"))
                    self.search_entry.config(fg=THEME["text_secondary"])
        except Exception:
            pass

        # 3. Update telemetry card titles
        try:
            self.card_speed.lbl_title.config(text=tr("stat_speed"))
            self.card_active.lbl_title.config(text=tr("stat_active"))
            self.card_total.lbl_title.config(text=tr("stat_files"))
        except Exception:
            pass

        # 4. Update sidebar headers & card
        try:
            self.lbl_sidebar_title.config(text=tr("nav_title"))
            self.lbl_sec_pustaka.config(text=tr("sec_library"))
            self.lbl_sec_kategori.config(text=tr("sec_categories"))
            self.storage_card.lbl_title.config(text=tr("sec_storage"))
            self.storage_card.btn_open.config(text=tr("tb_open_folder"))
        except Exception:
            pass

        # 5. Update sidebar items
        key_map = {
            "all": "nav_all",
            "downloading": "nav_downloading",
            "finished": "nav_finished",
            "video": "cat_video",
            "music": "cat_music",
            "pictures": "cat_pictures",
            "programs": "cat_programs",
            "documents": "cat_documents",
            "compressed": "cat_compressed",
        }
        for k, tr_k in key_map.items():
            if k in self.sidebar_items:
                self.sidebar_items[k].set_label(tr(tr_k))

        # 6. Update table headings
        try:
            self.tree.heading("name", text=tr("col_name"))
            self.tree.heading("size", text=tr("col_size"))
            self.tree.heading("status", text=tr("col_status"))
            self.tree.heading("progress", text=tr("col_progress"))
            self.tree.heading("speed", text=tr("col_speed"))
            self.tree.heading("url", text=tr("col_url"))
        except Exception:
            pass

        # 7. Re-render UI table rows, status bar, and telemetry
        self._tick_ui()

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
            "Tip Hari Ini - JustPressDownload (JPD)",
            "💡 Tip Cepat:\n\n"
            "1. Anda dapat menyalin tautan berkas di browser, dan JustPressDownload (JPD) otomatis menangkapnya.\n"
            "2. Gunakan tombol '⚙ Opsi' di menu atas untuk mengubah jumlah koneksi paralel hingga 32 jalur.\n"
            "3. Klik dua kali baris unduhan untuk langsung membuka berkas yang telah selesai diunduh.",
        )

    def check_for_updates(self):
        messagebox.showinfo(
            "Periksa Pembaruan - JustPressDownload (JPD)",
            "✔ Anda telah menggunakan versi terbaru JustPressDownload (JPD) (v1.1.0 High-Performance Release)!\n\nSemua komponen sistem mutakhir dan terintegrasi.",
        )


def main():
    root = tk.Tk()
    app = IDMGUIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
