"""
UI/UX Pro Max - Design Tokens and Unified Theme for IDM Clone
High-precision dark utility theme inspired by Windows modern design and classic IDM.
"""

import os
import sys
from typing import Callable, Optional, Any
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

# Cohesive Midnight Slate & Sapphire Palette (Elegant Modern Dark)
THEME = {
    # Surfaces (Layered Midnight Slate Undertones)
    "bg_dark": "#0f131d",          # Deep midnight slate: Window background
    "surface": "#1b2230",          # Elevated midnight slate: Toolbar, cards, dialogs
    "surface_alt": "#151b27",      # Inset midnight slate: Sidebar navigation
    "surface_canvas": "#0b0e15",   # Deepest abyss canvas for table
    "input_bg": "#090b10",         # Sunken deep field for text entries
    # Borders & Dividers
    "border": "#2d374d",           # Slate-700 hairline border
    "border_light": "#3e4c68",     # Muted slate divider
    "focus_ring": "#3b82f6",       # Luminous sapphire focus ring
    # Typography (Cool Slate Ramp - High Contrast HD)
    "text_primary": "#ffffff",     # Pure crisp high-contrast white
    "text_secondary": "#cbd5e1",   # Slate-300: High-contrast cool secondary labels (WCAG AAA)
    "text_tertiary": "#94a3b8",    # Slate-400: Captions & metadata (5.48:1 WCAG AA)
    "text_disabled": "#64748b",    # Slate-500: Disabled text
    # Semantic Colors (Single Brand Accent + Status)
    "accent_primary": "#2563eb",   # Sapphire Blue: 5.17:1 with white (WCAG AA)
    "accent_hover": "#1d4ed8",     # Deep Royal: 6.70:1 with white
    "accent_active": "#1e40af",    # 8.24:1 with white
    "secondary_bg": "#263145",     # Midnight slate secondary button
    "secondary_hover": "#33415c",
    "success": "#10b981",          # Emerald-500: Active speed / complete
    "warning": "#f59e0b",          # Amber-500: Security warning
    "danger": "#e11d48",           # Rose-600: Destructive action (4.70:1 with white)
    "danger_hover": "#be123c",     # 6.29:1 with white
    "danger_text": "#fb7185",      # Rose-400: High-contrast warning on card (5.92:1)
    # Component specifics
    "tree_bg": "#0b0e15",
    "tree_fg": "#f8fafc",
    "tree_select": "#2563eb",
    "tree_heading_bg": "#1b2230",
    "tree_heading_fg": "#ffffff",
    "progress_bg": "#0f131d",
    "progress_fill": "#2563eb",
    "progress_stripe": "#60a5fa",
    "part_divider": "#e11d48",
}

# Typography selection with native Windows ClearType subpixel hinting
FONT_DISPLAY = "Segoe UI" if sys.platform == "win32" else "SF Pro Display"
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "SF Pro Text"
FONT_TITLE = (FONT_DISPLAY, 12, "bold")
FONT_HEADING = (FONT_DISPLAY, 10, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_CODE = ("Consolas", 10)


def get_app_icon_path() -> Optional[str]:
    """Finds icon.ico path in project directories or bundled executable."""
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "icon.ico"))
        candidates.append(os.path.join(meipass, "..", "icon.ico"))
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "icon.ico"))
        candidates.append(os.path.join(exe_dir, "_internal", "icon.ico"))
    candidates.extend([
        os.path.abspath("icon.ico"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "icon.ico"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"),
    ])
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


def get_app_png_path() -> Optional[str]:
    """Finds icon.png path in project directories or bundled executable."""
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "icon.png"))
        candidates.append(os.path.join(meipass, "..", "icon.png"))
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "icon.png"))
        candidates.append(os.path.join(exe_dir, "_internal", "icon.png"))
    candidates.extend([
        os.path.abspath("icon.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "icon.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png"),
    ])
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


def apply_window_icon(window: Any):
    """Sets the custom 3D icon.ico and icon.png for the given window (Tk or Toplevel)."""
    ico = get_app_icon_path()
    png = get_app_png_path()

    # 1. Tkinter standard iconphoto with multiple resolutions (16x16, 24x24, 32x32, 48x48)
    if png and os.path.exists(png):
        try:
            from PIL import Image, ImageTk
            img = Image.open(png)
            master_w = window if isinstance(window, (tk.Tk, tk.Toplevel)) else None
            p16 = ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS), master=master_w)
            p24 = ImageTk.PhotoImage(img.resize((24, 24), Image.Resampling.LANCZOS), master=master_w)
            p32 = ImageTk.PhotoImage(img.resize((32, 32), Image.Resampling.LANCZOS), master=master_w)
            p48 = ImageTk.PhotoImage(img.resize((48, 48), Image.Resampling.LANCZOS), master=master_w)
            window.iconphoto(True, p16, p24, p32, p48)  # type: ignore[arg-type]
            setattr(window, "_app_icon_photo", p32)
            setattr(window, "_app_icon_photos", (p16, p24, p32, p48))
        except Exception:
            pass

    # 2. Windows native title bar icon via iconbitmap and direct WM_SETICON
    if ico and os.path.exists(ico):
        try:
            if isinstance(window, tk.Tk):
                try:
                    window.iconbitmap(default=ico)
                except Exception:
                    window.iconbitmap(ico)
            else:
                window.iconbitmap(ico)
        except Exception:
            pass

        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = window.winfo_id()
                parent_hwnd = user32.GetParent(hwnd)
                target_hwnd = parent_hwnd if parent_hwnd else hwnd

                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x00000010
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1

                h_small = user32.LoadImageW(None, ico, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                h_big = user32.LoadImageW(None, ico, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                if h_small:
                    user32.SendMessageW(target_hwnd, WM_SETICON, ICON_SMALL, h_small)
                if h_big:
                    user32.SendMessageW(target_hwnd, WM_SETICON, ICON_BIG, h_big)
            except Exception:
                pass


def apply_theme_to_toplevel(top: tk.Toplevel, width: int, height: int, title: str):
    """Sets standard background, icon, and centered geometry for a modal or dialog."""
    top.title(title)
    top.geometry(f"{width}x{height}")
    top.resizable(False, False)
    top.configure(bg=THEME["surface"])
    apply_window_icon(top)

    top.update_idletasks()
    try:
        screen_w = top.winfo_screenwidth()
        screen_h = top.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        top.geometry(f"{width}x{height}+{x}+{y}")
        top.deiconify()
        top.lift()
        top.focus_force()
    except Exception:
        pass


class Tooltip:
    """Lightweight tooltip appearing on hover after a delay (400ms)."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window: Optional[tk.Toplevel] = None
        self.id_after: Optional[str] = None

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        self._cancel()
        self.id_after = self.widget.after(self.delay, self._show)

    def _on_leave(self, event=None):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self.id_after:
            try:
                self.widget.after_cancel(self.id_after)
            except Exception:
                pass
            self.id_after = None

    def _show(self):
        if self.tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + (self.widget.winfo_width() // 2)
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg=THEME["border"])

        lbl = tk.Label(
            tw,
            text=self.text,
            background=THEME["surface"],
            foreground=THEME["text_primary"],
            font=FONT_SMALL,
            padx=8,
            pady=3,
            relief=tk.FLAT,
        )
        lbl.pack(padx=1, pady=1)

    def _hide(self):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


def draw_round_rectangle(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, r: int = 8, fill: str = "", outline: str = "", width: int = 1, **kwargs):
    """Draws a smooth anti-aliased rounded rectangle on a Tkinter Canvas."""
    r = min(r, abs(x2 - x1) // 2, abs(y2 - y1) // 2)
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, fill=fill, outline=outline, width=width, smooth=True, **kwargs)


_HD_PIL_CACHE: dict[tuple[str, int], Any] = {}


def get_hd_icon_image(name: str, size: int = 15) -> Optional[Any]:
    """Generates and caches an anti-aliased, 4x supersampled vector HD PIL image."""
    if not name:
        return None
    key = (name, size)
    if key in _HD_PIL_CACHE:
        return _HD_PIL_CACHE[key]

    try:
        from PIL import Image, ImageDraw
        scale = 4
        s = size * scale
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        if name == "resume":  # Sleek filled play triangle in vibrant emerald
            d.polygon([(s * 0.22, s * 0.16), (s * 0.84, s * 0.50), (s * 0.22, s * 0.84)], fill="#10b981")
            d.line([(s * 0.22, s * 0.16), (s * 0.84, s * 0.50)], fill="#6ee7b7", width=max(1, int(s * 0.05)))
        elif name == "pause":  # Two rounded vertical pause bars in amber gold
            w_bar = s * 0.22
            gap = s * 0.16
            r = s * 0.06
            x1 = (s - (w_bar * 2 + gap)) / 2
            d.rounded_rectangle([x1, s * 0.16, x1 + w_bar, s * 0.84], radius=r, fill="#f59e0b")
            d.line([x1 + 1, s * 0.16, x1 + w_bar - 1, s * 0.16], fill="#fde68a", width=max(1, int(s * 0.04)))
            x2 = x1 + w_bar + gap
            d.rounded_rectangle([x2, s * 0.16, x2 + w_bar, s * 0.84], radius=r, fill="#f59e0b")
            d.line([x2 + 1, s * 0.16, x2 + w_bar - 1, s * 0.16], fill="#fde68a", width=max(1, int(s * 0.04)))
        elif name == "add":  # Plus badge in white
            lw = max(2, int(s * 0.14))
            d.line([(s * 0.5, s * 0.16), (s * 0.5, s * 0.84)], fill="#ffffff", width=lw)
            d.line([(s * 0.16, s * 0.5), (s * 0.84, s * 0.5)], fill="#ffffff", width=lw)
        elif name == "stop":  # Rounded square in crimson/rose
            d.rounded_rectangle([s * 0.18, s * 0.18, s * 0.82, s * 0.82], radius=s * 0.10, fill="#f43f5e")
            d.line([(s * 0.20, s * 0.18), (s * 0.80, s * 0.18)], fill="#fda4af", width=max(1, int(s * 0.05)))
        elif name == "delete":  # Modern diagonal cross in crimson/rose
            lw = max(2, int(s * 0.14))
            d.line([(s * 0.22, s * 0.22), (s * 0.78, s * 0.78)], fill="#ffffff" if False else "#f43f5e", width=lw)
            d.line([(s * 0.22, s * 0.78), (s * 0.78, s * 0.22)], fill="#ffffff" if False else "#f43f5e", width=lw)
        elif name == "clear":  # Crisp checkmark in emerald
            lw = max(2, int(s * 0.14))
            d.line([(s * 0.16, s * 0.50), (s * 0.40, s * 0.76)], fill="#10b981", width=lw)
            d.line([(s * 0.40, s * 0.76), (s * 0.84, s * 0.24)], fill="#10b981", width=lw)
        elif name == "folder":  # Folder icon in sky blue
            d.rounded_rectangle([s * 0.14, s * 0.30, s * 0.86, s * 0.82], radius=s * 0.08, fill="#38bdf8")
            d.polygon([(s * 0.14, s * 0.30), (s * 0.44, s * 0.30), (s * 0.52, s * 0.42), (s * 0.14, s * 0.42)], fill="#7dd3fc")
        elif name == "settings":  # Gear cogwheel in steel slate
            d.ellipse([s * 0.24, s * 0.24, s * 0.76, s * 0.76], outline="#94a3b8", width=max(2, int(s * 0.12)))
            d.ellipse([s * 0.38, s * 0.38, s * 0.62, s * 0.62], fill="#1e293b")
            d.rectangle([s * 0.44, s * 0.10, s * 0.56, s * 0.26], fill="#94a3b8")
            d.rectangle([s * 0.44, s * 0.74, s * 0.56, s * 0.90], fill="#94a3b8")
            d.rectangle([s * 0.10, s * 0.44, s * 0.26, s * 0.56], fill="#94a3b8")
            d.rectangle([s * 0.74, s * 0.44, s * 0.90, s * 0.56], fill="#94a3b8")
        elif name == "more":  # Double chevron
            lw = max(2, int(s * 0.12))
            d.line([(s * 0.28, s * 0.25), (s * 0.52, s * 0.50), (s * 0.28, s * 0.75)], fill="#cbd5e1", width=lw)
            d.line([(s * 0.48, s * 0.25), (s * 0.72, s * 0.50), (s * 0.48, s * 0.75)], fill="#cbd5e1", width=lw)

        res = im.resize((size, size), Image.Resampling.LANCZOS)
        _HD_PIL_CACHE[key] = res
        return res
    except Exception:
        return None


class RoundedButton(tk.Canvas):
    """Tactile rounded button built on Tkinter Canvas with 3D elevation and smooth hover transitions."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Optional[Callable] = None,
        kind: str = "secondary",  # 'primary', 'secondary', 'danger', 'toolbar'
        width: Optional[int] = None,
        padx: int = 12,
        pady: int = 5,
        radius: int = 7,
        tooltip: Optional[str] = None,
        icon: Optional[str] = None,
    ):
        self.parent = parent
        self.text = text
        self.command = command
        self.kind = kind
        self.radius = radius
        self.padx = padx
        self.pady = pady
        self.state = "normal"
        self.custom_width = width
        self.icon = icon
        self._icon_ref: Optional[Any] = None

        # Resolve parent background so canvas blends seamlessly
        if hasattr(parent, "cget"):
            try:
                self.bg_parent = parent.cget("bg")
            except Exception:
                self.bg_parent = THEME["surface"]
        else:
            self.bg_parent = THEME["surface"]

        if kind == "primary":
            self.bg_normal = THEME["accent_primary"]
            self.bg_hover = THEME["accent_hover"]
            self.bg_active = THEME["accent_active"]
            self.top_highlight = "#60a5fa"
            self.bot_shadow = "#05080f"
            self.border_col = "#1d4ed8"
            self.fg = "#ffffff"
            self.font = FONT_HEADING
        elif kind == "danger":
            self.bg_normal = THEME["danger"]
            self.bg_hover = THEME["danger_hover"]
            self.bg_active = "#8b0000"
            self.top_highlight = "#fb7185"
            self.bot_shadow = "#05080f"
            self.border_col = "#9f1239"
            self.fg = "#ffffff"
            self.font = FONT_BODY
        elif kind == "toolbar":
            self.bg_normal = THEME["surface"]
            self.bg_hover = THEME["secondary_hover"]
            self.bg_active = THEME["accent_primary"]
            self.top_highlight = "#384661"
            self.bot_shadow = "#080c14"
            self.border_col = "#243249"
            self.fg = THEME["text_primary"]
            self.font = FONT_BODY
        else:  # secondary
            self.bg_normal = THEME["secondary_bg"]
            self.bg_hover = THEME["secondary_hover"]
            self.bg_active = "#2c2c2e"
            self.top_highlight = "#3e4f6d"
            self.bot_shadow = "#080c14"
            self.border_col = "#243249"
            self.fg = THEME["text_primary"]
            self.font = FONT_BODY

        try:
            font_obj = tkfont.Font(font=self.font)
            self.text_w = font_obj.measure(self.text) if self.text else 0
            self.text_h = font_obj.metrics("linespace")
        except Exception:
            self.text_w = max(40, len(self.text) * 8) if self.text else 0
            self.text_h = 18

        icon_space = 22 if self.icon else 0
        self.total_w = self.custom_width if self.custom_width else (self.text_w + icon_space + (self.padx * 2))
        self.total_h = max(28, self.text_h + (self.pady * 2))

        super().__init__(
            parent,
            width=self.total_w,
            height=self.total_h,
            bg=self.bg_parent,
            highlightthickness=0,
            cursor="hand2",
        )

        self._draw(self.bg_normal)

        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Button-1>", self._on_press, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")

        if tooltip:
            Tooltip(self, tooltip)

    def _get_icon_photo(self, icon_name: Optional[str], size: int = 15) -> Optional[Any]:
        if not icon_name:
            return None
        if not hasattr(self, "_icon_photos"):
            self._icon_photos = {}
        key = (icon_name, size)
        if key in self._icon_photos:
            return self._icon_photos[key]
        try:
            from PIL import ImageTk
            pil_img = get_hd_icon_image(icon_name, size)
            if pil_img:
                photo = ImageTk.PhotoImage(pil_img, master=self)
                self._icon_photos[key] = photo
                return photo
        except Exception:
            pass
        return None

    def _draw(self, fill_color, is_pressed: bool = False):
        self.delete("all")
        w, h = self.total_w, self.total_h
        r = self.radius
        y_offset = 1 if is_pressed else 0

        if is_pressed:
            # Pressed state: sinks down slightly, darker inner border
            draw_round_rectangle(self, 1, 2, w - 1, h, r=r, fill=fill_color, outline=self.bot_shadow, width=1)
        else:
            # 1. Subtle drop shadow for 3D elevation
            draw_round_rectangle(self, 1, 2, w - 1, h, r=r, fill=self.bot_shadow, outline="")
            # 2. Main rounded body with border
            draw_round_rectangle(self, 1, 1, w - 1, h - 1, r=r, fill=fill_color, outline=self.border_col, width=1)
            # 3. Overhead specular highlight line across the top edge
            if w > 2 * r and h > 10:
                self.create_line(r + 2, 2, w - r - 2, 2, fill=self.top_highlight, width=1.5)

        # 4. Icon and Text rendering
        icon_photo = self._get_icon_photo(self.icon, size=15) if self.icon else None

        if icon_photo and self.text:
            content_w = 15 + 6 + self.text_w
            x_start = max(self.padx, (w - content_w) // 2)
            self.create_image(x_start + 7, (h // 2) + y_offset, image=icon_photo)
            self.create_text(x_start + 15 + 6, (h // 2) + y_offset, text=self.text, fill=self.fg, font=self.font, anchor=tk.W)
            self._icon_ref = icon_photo
        elif icon_photo and not self.text:
            self.create_image(w // 2, (h // 2) + y_offset, image=icon_photo)
            self._icon_ref = icon_photo
        else:
            self.create_text(w // 2, (h // 2) + y_offset, text=self.text, fill=self.fg, font=self.font, anchor=tk.CENTER)

    def _on_enter(self, e):
        if self.state != "disabled":
            self._draw(self.bg_hover, is_pressed=False)

    def _on_leave(self, e):
        if self.state != "disabled":
            self._draw(self.bg_normal, is_pressed=False)

    def _on_press(self, e):
        if self.state != "disabled":
            self._draw(self.bg_active, is_pressed=True)

    def _on_release(self, e):
        if self.state != "disabled":
            self._draw(self.bg_hover, is_pressed=False)
            if self.command:
                self.command()

    def config(self, **kwargs):
        if "text" in kwargs or "icon" in kwargs:
            if "text" in kwargs:
                self.text = kwargs["text"]
            if "icon" in kwargs:
                self.icon = kwargs["icon"]
            try:
                font_obj = tkfont.Font(font=self.font)
                self.text_w = font_obj.measure(self.text) if self.text else 0
            except Exception:
                self.text_w = max(40, len(self.text) * 8) if self.text else 0
            icon_space = 22 if self.icon else 0
            self.total_w = self.custom_width if self.custom_width else (self.text_w + icon_space + (self.padx * 2))
            super().config(width=self.total_w)
            self._draw(self.bg_normal)
        if "state" in kwargs:
            self.state = kwargs["state"]
            self.config(cursor="hand2" if self.state != "disabled" else "arrow")
        if "command" in kwargs:
            self.command = kwargs["command"]
        canvas_kwargs = {k: v for k, v in kwargs.items() if k not in ("text", "state", "command", "icon")}
        if canvas_kwargs:
            super().config(**canvas_kwargs)

    def cget(self, key):
        if key == "text":
            return self.text
        if key == "state":
            return self.state
        if key == "command":
            return self.command
        if key == "icon":
            return self.icon
        return super().cget(key)


def create_modern_button(
    parent: tk.Widget,
    text: str,
    command: Optional[Callable] = None,
    kind: str = "secondary",  # 'primary', 'secondary', 'danger', 'toolbar'
    width: Optional[int] = None,
    padx: int = 12,
    pady: int = 4,
    tooltip: Optional[str] = None,
    radius: int = 7,
    icon: Optional[str] = None,
) -> RoundedButton:
    """Creates a tactile, beautifully styled rounded button with active hover animations."""
    return RoundedButton(
        parent=parent,
        text=text,
        command=command,
        kind=kind,
        width=width,
        padx=padx,
        pady=pady,
        radius=radius,
        tooltip=tooltip,
        icon=icon,
    )


def setup_global_ttk_theme():
    """Configures ttk styles for treeviews, notebooks, and progressbars to match dark mode."""
    style = ttk.Style()
    style.theme_use("clam")

    # Dark Treeview
    style.configure(
        "Treeview",
        background=THEME["tree_bg"],
        foreground=THEME["tree_fg"],
        fieldbackground=THEME["tree_bg"],
        rowheight=28,
        font=FONT_BODY,
        borderwidth=0,
        lightcolor=THEME["tree_bg"],
        darkcolor=THEME["tree_bg"],
        bordercolor=THEME["tree_bg"],
    )
    style.map(
        "Treeview",
        background=[("selected", THEME["tree_select"])],
        foreground=[("selected", "#ffffff")],
        lightcolor=[("!disabled", THEME["tree_bg"])],
        darkcolor=[("!disabled", THEME["tree_bg"])],
        bordercolor=[("!disabled", THEME["tree_bg"])],
    )

    # Treeview Headings (eliminating raw white/light gray bordercolor in clam)
    style.configure(
        "Treeview.Heading",
        background=THEME["tree_heading_bg"],
        foreground=THEME["tree_heading_fg"],
        font=FONT_HEADING,
        relief="flat",
        borderwidth=0,
        padding=[6, 4],
        lightcolor=THEME["tree_heading_bg"],
        darkcolor=THEME["tree_heading_bg"],
        bordercolor=THEME["tree_heading_bg"],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", THEME["secondary_hover"])],
        lightcolor=[("!disabled", THEME["tree_heading_bg"])],
        darkcolor=[("!disabled", THEME["tree_heading_bg"])],
        bordercolor=[("!disabled", THEME["tree_heading_bg"])],
    )

    # Dark Scrollbar styling
    style.configure(
        "Vertical.TScrollbar",
        background=THEME["surface"],
        troughcolor=THEME["tree_bg"],
        bordercolor=THEME["tree_bg"],
        arrowcolor=THEME["text_secondary"],
        relief="flat",
        borderwidth=0,
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", THEME["secondary_hover"]), ("!disabled", THEME["surface"])],
        troughcolor=[("!disabled", THEME["tree_bg"])],
        bordercolor=[("!disabled", THEME["tree_bg"])],
    )

    # Dark Notebook Tabs
    style.configure(
        "Options.TNotebook",
        background=THEME["surface"],
        borderwidth=0,
    )
    style.configure(
        "Options.TNotebook.Tab",
        background=THEME["surface_alt"],
        foreground=THEME["text_secondary"],
        padding=[14, 6],
        font=FONT_HEADING,
        borderwidth=0,
    )
    style.map(
        "Options.TNotebook.Tab",
        background=[("selected", THEME["surface"]), ("active", THEME["secondary_hover"])],
        foreground=[("selected", THEME["text_primary"]), ("active", "#ffffff")],
    )

    # Combobox Dark Theme
    style.configure(
        "TCombobox",
        fieldbackground=THEME["input_bg"],
        background=THEME["surface_alt"],
        foreground=THEME["text_primary"],
        selectbackground=THEME["tree_select"],
        selectforeground="#ffffff",
        arrowcolor=THEME["text_primary"],
        borderwidth=0,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", THEME["input_bg"]), ("!disabled", THEME["input_bg"])],
        background=[("readonly", THEME["surface_alt"]), ("!disabled", THEME["surface_alt"])],
        foreground=[("readonly", THEME["text_primary"]), ("!disabled", THEME["text_primary"])],
        selectbackground=[("readonly", THEME["tree_select"])],
        selectforeground=[("readonly", "#ffffff")],
        arrowcolor=[("readonly", THEME["text_primary"]), ("!disabled", THEME["text_primary"])],
    )


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    clean = h.lstrip("#")
    if len(clean) == 3:
        clean = "".join([c * 2 for c in clean])
    return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r = max(0, min(255, int(rgb[0])))
    g = max(0, min(255, int(rgb[1])))
    b = max(0, min(255, int(rgb[2])))
    return f"#{r:02x}{g:02x}{b:02x}"


def interpolate_color(c1_hex: str, c2_hex: str, t: float) -> str:
    """Linearly interpolate between two hex color codes with factor t (0.0 to 1.0)."""
    factor = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = hex_to_rgb(c1_hex)
    r2, g2, b2 = hex_to_rgb(c2_hex)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return rgb_to_hex((r, g, b))
