"""
UI/UX Pro Max - Design Tokens and Unified Theme for IDM Clone
High-precision dark utility theme inspired by Windows modern design and classic IDM.
"""

import os
import sys
import time
import math
from typing import Callable, Optional, Any
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

# Liquid Glass Design System Tokens (Apple-grade Translucent & Frosted Glass)
THEME = {
    # Surfaces (Liquid Glass Translucent Hierarchy)
    "bg_dark": "#07090e",          # Deep abyss backdrop
    "surface": "#121b2d",          # L2 Frosted Glass: Toolbar, cards, dialogs
    "surface_alt": "#0d1524",      # L1 Inset Nav Glass: Sidebar navigation
    "surface_canvas": "#070a10",   # Deepest abyss canvas for table viewport
    "input_bg": "#090f1a",         # Inset dark glass for inputs & counter badges
    # Ambient Mesh Lighting Orbs
    "mesh_sapphire": "#0a1e3f",    # Cool sapphire ambient light
    "mesh_violet": "#13112c",      # Soft violet ambient light
    "mesh_teal": "#071f33",        # Deep ocean teal ambient glow
    # Glass Rims & Specular Refraction
    "glass_rim": "#ffffff",        # 1px overhead specular highlight
    "glass_refraction": "#38bdf8", # 1px cyan edge refraction
    "glass_border": "#1e2e46",     # Muted glass structural border
    "glass_border_hover": "#38bdf8", # Glow ring on hover
    "glass_shadow_ambient": "#010204", # Diffused soft ambient shadow
    "glass_shadow_contact": "#03050a", # Close contact shadow
    "glass_shadow": "#020306",     # Legacy alias
    # Focus Ring Tokens
    "focus_ring": "#38bdf8",       # Luminous sapphire focus ring
    "focus_ring_outer": "#1e3a5f", # Outer soft focus ring halo
    # Disabled State Tokens
    "disabled_text": "#526075",    # Slate-500 dimmed text
    "disabled_bg": "#090e18",      # Inactive glass surface
    "disabled_border": "#151f2e",  # Inactive glass border
    # Borders & Dividers
    "border": "#1e2e46",           # Slate-700 glass hairline border
    "border_light": "#2a3d5b",     # Muted slate glass divider
    # Typography (High Contrast Glass Readable - Verified WCAG AA/AAA)
    "text_primary": "#ffffff",     # Pure crisp high-contrast white (19.57:1)
    "text_secondary": "#cbd5e1",   # Slate-300: High-contrast cool secondary labels (13.18:1)
    "text_tertiary": "#94a3b8",    # Slate-400: Captions & metadata (7.63:1)
    "text_subtle": "#7c8ba1",      # Slate-450: URL & subtle metadata (> 4.5:1 WCAG AA: 5.65:1)
    "text_disabled": "#526075",    # Dimmed disabled text
    # Semantic Colors (Single Brand Accent + Status)
    "accent_primary": "#007aff",   # Apple Sapphire Blue CTA
    "accent_hover": "#0284c7",     # Vivid Cyan-Blue hover
    "accent_active": "#0369a1",    # Pressed deep sapphire
    "accent_glow": "#38bdf8",      # Neon cyan edge glow
    "secondary_bg": "#162338",     # Frosted secondary glass button
    "secondary_hover": "#1e3250",  # Luminous secondary hover
    "success": "#10b981",          # Emerald-500: Active speed / complete
    "success_glow": "#34d399",     # Emerald neon specular
    "warning": "#f59e0b",          # Amber-500: Security warning
    # Destructive Action Tokens (Delete)
    "danger": "#f43f5e",           # Rose-500: Destructive action
    "danger_glow": "#f43f5e",      # Rose neon edge glow
    "danger_surface": "#4c0519",   # Deep translucent rose glass
    "danger_hover": "#881337",     # Rose-800 hover
    "danger_active": "#300310",    # Pressed deep rose
    "danger_border": "#be123c",    # Rose-700 structural border
    "danger_rim": "#fda4af",       # Rose specular rim
    "danger_text": "#ffffff",      # White on destructive buttons
    # Component specifics
    "tree_bg": "#080c14",
    "tree_fg": "#f8fafc",
    "tree_select": "#007aff",
    "tree_heading_bg": "#121b2d",
    "tree_heading_fg": "#ffffff",
    "progress_bg": "#090f1a",
    "progress_fill": "#007aff",
    "progress_stripe": "#38bdf8",
    "part_divider": "#f43f5e",
}

# Radius Tokens (Apple Glass Curvature Hierarchy)
RADIUS_XS = 8
RADIUS_SM = 12
RADIUS_MD = 16
RADIUS_LG = 20
RADIUS_XL = 24
RADIUS_2XL = 28
RADIUS_PILL = 9999

# Motion Tokens
MOTION_HOVER_MS = 160
MOTION_SPRING_TRAY = 0.22


def is_reduced_motion() -> bool:
    """Checks if the user prefers reduced motion (via env or config)."""
    if os.environ.get("REDUCED_MOTION", "").lower() in ("1", "true", "yes"):
        return True
    try:
        from idm_gui.settings import settings
        return bool(settings.data.get("reduced_motion", False))
    except Exception:
        return False


def get_window_dpi(window: Any = None) -> int:
    """Returns the effective DPI for the window on Windows (e.g. 96=100%, 120=125%, 144=150%)."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = 0
            if window and hasattr(window, "winfo_id"):
                hwnd = window.winfo_id()
            if hwnd > 0 and hasattr(user32, "GetDpiForWindow"):
                dpi = user32.GetDpiForWindow(hwnd)
                if dpi > 0:
                    return int(dpi)
            if hasattr(user32, "GetDpiForSystem"):
                dpi = user32.GetDpiForSystem()
                if dpi > 0:
                    return int(dpi)
        except Exception:
            pass
    return 96


def get_dpi_scale(window: Any = None) -> float:
    """Returns DPI scaling multiplier (1.0 = 100%, 1.25 = 125%, 1.5 = 150%)."""
    return get_window_dpi(window) / 96.0


def scale_px(val: int, window: Any = None, scale: Optional[float] = None) -> int:
    """Scales a pixel dimension safely according to monitor DPI scaling (125%/150%)."""
    s = scale if scale is not None else get_dpi_scale(window)
    return max(1, int(round(val * s)))

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


def _apply_win32_native_icon(window: Any):
    """Binds the high-DPI multi-res .ico directly to the top-level Win32 window frame and class."""
    if sys.platform != "win32":
        return
    ico = get_app_icon_path()
    if not ico or not os.path.exists(ico):
        return

    try:
        import ctypes
        user32 = ctypes.windll.user32
        GA_ROOT = 2
        WM_SETICON = 0x0080
        GCLP_HICONSM = -34
        GCLP_HICON = -14
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010

        hwnd = window.winfo_id()
        top_hwnd = user32.GetAncestor(hwnd, GA_ROOT)
        frame_hwnd = None
        if hasattr(window, "wm_frame"):
            try:
                frame_hwnd = int(window.wm_frame(), 16)
            except Exception:
                frame_hwnd = None

        targets = set()
        for h in (frame_hwnd, top_hwnd, hwnd):
            if h and h > 0:
                targets.add(h)

        for target in targets:
            sm_w = user32.GetSystemMetrics(49) if hasattr(user32, "GetSystemMetrics") else 16
            sm_h = user32.GetSystemMetrics(50) if hasattr(user32, "GetSystemMetrics") else 16
            lg_w = user32.GetSystemMetrics(11) if hasattr(user32, "GetSystemMetrics") else 32
            lg_h = user32.GetSystemMetrics(12) if hasattr(user32, "GetSystemMetrics") else 32

            h_small = user32.LoadImageW(None, ico, IMAGE_ICON, sm_w, sm_h, LR_LOADFROMFILE)
            h_big = user32.LoadImageW(None, ico, IMAGE_ICON, lg_w, lg_h, LR_LOADFROMFILE)

            if h_small:
                user32.SendMessageW(target, WM_SETICON, 0, h_small)
                user32.SetClassLongPtrW(target, GCLP_HICONSM, h_small)
            if h_big:
                user32.SendMessageW(target, WM_SETICON, 1, h_big)
                user32.SetClassLongPtrW(target, GCLP_HICON, h_big)
    except Exception:
        pass


def apply_window_icon(window: Any):
    """Sets the custom 3D icon.ico and icon.png for the given window (Tk or Toplevel)."""
    ico = get_app_icon_path()
    png = get_app_png_path()

    # 1. Tkinter standard iconphoto with multiple resolutions (16x16, 24x24, 32x32, 48x48)
    if png and os.path.exists(png) and not getattr(window, "_icon_photo_applied", False):
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
            setattr(window, "_icon_photo_applied", True)
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

        # Immediate and staged deferred applications so newly created DWM frames receive the icon
        _apply_win32_native_icon(window)
        try:
            window.after(50, lambda: _apply_win32_native_icon(window))
            window.after(250, lambda: _apply_win32_native_icon(window))
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
        setattr(widget, "tooltip_obj", self)

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        self._cancel()
        self.id_after = self.widget.after(self.delay, self._show)

    def _on_leave(self, event=None):
        self._cancel()
        self._hide()

    def set_text(self, text: str):
        self.text = text
        if self.tip_window:
            for child in self.tip_window.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(text=text)

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


def draw_liquid_glass_panel(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    r: int = RADIUS_LG,
    fill: str = THEME["surface"],
    border: str = THEME["glass_border"],
    rim_highlight: str = THEME["glass_rim"],
    refraction: str = THEME["glass_refraction"],
    shadow: bool = True,
    width: int = 1,
    tags: str = "",
) -> list[int]:
    """Draws a modern Apple Liquid Glass panel with multi-layer shadow, frosted body,
    1px top specular highlight rim, and bottom refraction glow."""
    item_ids = []
    t_arg = (tags,) if tags else ()
    # 1. Soft layered ambient drop shadow
    if shadow:
        s1 = draw_round_rectangle(canvas, x1, y1 + 4, x2, y2 + 4, r=r, fill="#020306", outline="", tags=t_arg)
        s2 = draw_round_rectangle(canvas, x1, y1 + 2, x2, y2 + 2, r=r, fill="#04060c", outline="", tags=t_arg)
        item_ids.extend([s1, s2])
    # 2. Main frosted glass body with structural border
    main_body = draw_round_rectangle(canvas, x1, y1, x2, y2, r=r, fill=fill, outline=border, width=width, tags=t_arg)
    item_ids.append(main_body)
    # 3. Overhead specular reflection (frosted rim across the top curvature)
    if (x2 - x1) > (2 * r) and (y2 - y1) > 10:
        top_rim = canvas.create_line(x1 + r, y1 + 1, x2 - r, y1 + 1, fill=rim_highlight, width=1, tags=t_arg)
        item_ids.append(top_rim)
        # 4. Subtle bottom refraction sheen
        if refraction:
            bot_rim = canvas.create_line(x1 + r, y2 - 1, x2 - r, y2 - 1, fill=refraction, width=1, tags=t_arg)
            item_ids.append(bot_rim)
    return item_ids


def draw_skeleton_shimmer(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    r: int = RADIUS_SM,
    phase: float = 0.5,
    base_color: str = "#0d1524",
    shimmer_color: str = "#1e2e4a",
    tags: str = "",
):
    """Draws a shimmering skeleton loader bar with animated specular wave."""
    t_arg = (tags,) if tags else ()
    draw_round_rectangle(canvas, x1, y1, x2, y2, r=r, fill=base_color, outline="", tags=t_arg)
    w = max(10, x2 - x1)
    shimmer_w = max(20, int(w * 0.35))
    offset = int(phase * (w + shimmer_w)) - shimmer_w
    sx1 = max(x1, x1 + offset)
    sx2 = min(x2, x1 + offset + shimmer_w)
    if sx2 > sx1:
        canvas.create_rectangle(sx1, y1, sx2, y2, fill=shimmer_color, outline="", tags=t_arg)


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


class RoundedButton(tk.Canvas):
    """Modern Apple Liquid Glass button with specular rim, refraction highlight,
    subtle drop shadow, and smooth animated hover glow."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Optional[Callable] = None,
        kind: str = "secondary",  # 'primary', 'secondary', 'danger', 'toolbar'
        width: Optional[int] = None,
        padx: int = 12,
        pady: int = 5,
        radius: int = RADIUS_MD,
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
        self._anim_id: Optional[str] = None
        self._glow_alpha: float = 0.0

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
            self.top_highlight = "#93c5fd"
            self.bot_shadow = THEME["glass_shadow_ambient"]
            self.border_col = THEME["accent_primary"]
            self.border_hover = THEME["accent_glow"]
            self.refraction_col = THEME["accent_glow"]
            self.fg = "#ffffff"
            self.font = FONT_HEADING
        elif kind == "danger":
            self.bg_normal = THEME["danger_surface"]
            self.bg_hover = THEME["danger_hover"]
            self.bg_active = THEME["danger_active"]
            self.top_highlight = THEME["danger_rim"]
            self.bot_shadow = THEME["glass_shadow_ambient"]
            self.border_col = THEME["danger_border"]
            self.border_hover = THEME["danger_glow"]
            self.refraction_col = THEME["danger_glow"]
            self.fg = THEME["danger_text"]
            self.font = FONT_BODY
        elif kind == "toolbar":
            self.bg_normal = THEME["surface"]
            self.bg_hover = THEME["secondary_hover"]
            self.bg_active = THEME["accent_primary"]
            self.top_highlight = "#475569"
            self.bot_shadow = THEME["glass_shadow_ambient"]
            self.border_col = THEME["glass_border"]
            self.border_hover = THEME["accent_glow"]
            self.refraction_col = THEME["glass_border_hover"]
            self.fg = THEME["text_primary"]
            self.font = FONT_BODY
        else:  # secondary
            self.bg_normal = THEME["secondary_bg"]
            self.bg_hover = THEME["secondary_hover"]
            self.bg_active = "#0f1a2b"
            self.top_highlight = "#64748b"
            self.bot_shadow = THEME["glass_shadow_ambient"]
            self.border_col = "#243650"
            self.border_hover = THEME["accent_glow"]
            self.refraction_col = "#1e3a5f"
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

        self.is_focused = False
        self._draw(self.bg_normal)

        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Button-1>", self._on_press, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        self.bind("<FocusIn>", lambda e: self._on_focus(True), add="+")
        self.bind("<FocusOut>", lambda e: self._on_focus(False), add="+")

        self.tooltip_obj: Optional[Tooltip] = None
        if tooltip:
            self.tooltip_obj = Tooltip(self, tooltip)

    def set_tooltip(self, text: Optional[str]):
        if text:
            if self.tooltip_obj:
                self.tooltip_obj.set_text(text)
            else:
                self.tooltip_obj = Tooltip(self, text)
        else:
            if self.tooltip_obj:
                self.tooltip_obj.set_text("")

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

    def _draw(self, fill_color: str, is_pressed: bool = False, glow_alpha: float = 0.0):
        self.delete("all")
        w, h = self.total_w, self.total_h
        r = self.radius
        y_offset = 1 if is_pressed else 0

        border_active = interpolate_color(self.border_col, self.border_hover, glow_alpha) if glow_alpha > 0 else self.border_col

        if self.state == "disabled":
            fill_color = THEME["disabled_bg"]
            border_active = THEME["disabled_border"]
            text_fg = THEME["disabled_text"]
            # Main frosted disabled body
            draw_round_rectangle(self, 1, 1, w - 1, h - 1, r=r, fill=fill_color, outline=border_active, width=1)
        elif is_pressed:
            text_fg = self.fg
            # Pressed state: sinks down 1px with deepened core & contact border
            draw_round_rectangle(self, 1, 2, w - 1, h, r=r, fill=fill_color, outline=self.bot_shadow, width=1)
        else:
            text_fg = self.fg
            # 1. Soft layered ambient drop shadow
            draw_round_rectangle(self, 1, 3, w - 1, h, r=r, fill=self.bot_shadow, outline="")
            draw_round_rectangle(self, 1, 2, w - 1, h, r=r, fill=THEME["glass_shadow_contact"], outline="")
            # 2. Focus ring if focused
            if getattr(self, "is_focused", False):
                draw_round_rectangle(self, 0, 0, w, h, r=r + 1, fill="", outline=THEME["focus_ring"], width=2)
            # 3. Outer luminous glow ring when hovered
            elif glow_alpha > 0.05:
                draw_round_rectangle(self, 0, 0, w, h, r=r + 1, fill="", outline=border_active, width=1)
            # 4. Main frosted glass container with structural border
            draw_round_rectangle(self, 1, 1, w - 1, h - 1, r=r, fill=fill_color, outline=border_active, width=1)
            # 5. Overhead specular highlight line across top curve (Apple Frosted Rim)
            if w > 2 * r and h > 10:
                self.create_line(r + 2, 2, w - r - 2, 2, fill=self.top_highlight, width=1)
            # 6. Subtle bottom refraction sheen
            if self.refraction_col and w > 2 * r:
                self.create_line(r + 3, h - 2, w - r - 3, h - 2, fill=self.refraction_col, width=1)

        # 7. Icon and Text rendering
        icon_photo = self._get_icon_photo(self.icon, size=15) if self.icon else None

        if icon_photo and self.text:
            content_w = 15 + 6 + self.text_w
            x_start = max(self.padx, (w - content_w) // 2)
            self.create_image(x_start + 7, (h // 2) + y_offset, image=icon_photo)
            self.create_text(x_start + 15 + 6, (h // 2) + y_offset, text=self.text, fill=text_fg, font=self.font, anchor=tk.W)
            self._icon_ref = icon_photo
        elif icon_photo and not self.text:
            self.create_image(w // 2, (h // 2) + y_offset, image=icon_photo)
            self._icon_ref = icon_photo
        else:
            self.create_text(w // 2, (h // 2) + y_offset, text=self.text, fill=text_fg, font=self.font, anchor=tk.CENTER)

    def _on_focus(self, focused: bool):
        self.is_focused = focused
        self._draw(self.bg_hover if self._glow_alpha > 0.5 else self.bg_normal, glow_alpha=self._glow_alpha)

    def _animate_hover(self, target_hover: bool):
        if self._anim_id is not None:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

        if is_reduced_motion() or os.environ.get("PYTEST_CURRENT_TEST"):
            self._glow_alpha = 1.0 if target_hover else 0.0
            self._draw(self.bg_hover if target_hover else self.bg_normal, is_pressed=False, glow_alpha=self._glow_alpha)
            return

        total_steps = 4
        start_alpha = self._glow_alpha
        target_alpha = 1.0 if target_hover else 0.0

        def _step(step_idx: int):
            self._anim_id = None
            if not self.winfo_exists():
                return
            t = (step_idx + 1) / total_steps
            # Ease out deceleration
            p = 1.0 - (1.0 - t) ** 2
            self._glow_alpha = start_alpha + (target_alpha - start_alpha) * p
            cur_fill = interpolate_color(self.bg_normal, self.bg_hover, self._glow_alpha)
            self._draw(cur_fill, is_pressed=False, glow_alpha=self._glow_alpha)
            if step_idx + 1 < total_steps:
                self._anim_id = self.after(35, lambda: _step(step_idx + 1))

        _step(0)

    def _on_enter(self, e):
        if self.state != "disabled":
            self._animate_hover(True)

    def _on_leave(self, e):
        if self.state != "disabled":
            self._animate_hover(False)

    def _on_press(self, e):
        if self.state != "disabled":
            self._draw(self.bg_active, is_pressed=True, glow_alpha=1.0)

    def _on_release(self, e):
        if self.state != "disabled":
            self._draw(self.bg_hover, is_pressed=False, glow_alpha=self._glow_alpha)
            if self.command:
                self.command()

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        self.config(**kwargs)

    def config(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            super().config(cursor="hand2" if self.state != "disabled" else "arrow")
            self._draw(self.bg_normal)
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
        if "command" in kwargs:
            self.command = kwargs["command"]
        if "tooltip" in kwargs:
            self.set_tooltip(kwargs.pop("tooltip"))
        canvas_kwargs = {k: v for k, v in kwargs.items() if k not in ("text", "state", "command", "icon", "tooltip")}
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
        if key == "tooltip":
            return self.tooltip_obj.text if self.tooltip_obj else ""
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
    radius: int = RADIUS_MD,
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


class GlassThinScrollbar(tk.Canvas):
    """Ultra-sleek auto-hiding floating scrollbar for Liquid Glass surfaces."""

    def __init__(self, parent: tk.Widget, command: Optional[Callable] = None, width: int = 6, **kwargs):
        bg = kwargs.pop("bg", THEME["surface_canvas"])
        super().__init__(parent, width=width, bg=bg, highlightthickness=0, **kwargs)
        self.command = command
        self.bar_width = width
        self.first = 0.0
        self.last = 1.0
        self.thumb_color = "#1e3a5f"
        self.hover_color = THEME["accent_glow"]
        self.active_color = self.thumb_color
        self._fade_id: Optional[str] = None
        self._dragging: bool = False
        self._drag_start_y: int = 0

        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Button-1>", self._on_press, add="+")
        self.bind("<B1-Motion>", self._on_drag, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        self.bind("<Configure>", lambda e: self._redraw(), add="+")

    def set(self, first: float | str, last: float | str):
        self.first = float(first)
        self.last = float(last)
        self._show_and_schedule_fade()
        self._redraw()

    def _show_and_schedule_fade(self):
        if self._fade_id is not None:
            try:
                self.after_cancel(self._fade_id)
            except Exception:
                pass
            self._fade_id = None
        self.active_color = self.thumb_color
        self._fade_id = self.after(1500, self._hide_thumb)

    def _hide_thumb(self):
        self._fade_id = None
        if not self._dragging:
            self.delete("thumb")

    def _on_enter(self, e):
        self.active_color = self.hover_color
        self._redraw()

    def _on_leave(self, e):
        self.active_color = self.thumb_color
        self._redraw()

    def _on_press(self, e):
        self._dragging = True
        self._drag_start_y = e.y
        self.active_color = self.hover_color
        self._redraw()

    def _on_drag(self, e):
        h = self.winfo_height()
        if h > 0 and self.command:
            frac = max(0.0, min(1.0, e.y / h))
            self.command("moveto", frac)

    def _on_release(self, e):
        self._dragging = False
        self._show_and_schedule_fade()
        self._redraw()

    def _redraw(self):
        self.delete("thumb")
        h = self.winfo_height()
        w = self.bar_width
        if h < 20 or (self.last - self.first) >= 0.999:
            return
        top = int(self.first * h)
        bot = max(top + 20, int(self.last * h))
        draw_round_rectangle(self, 1, top, w - 1, bot, r=min(w // 2, 4), fill=self.active_color, outline="", tags="thumb")


class GlassSearchEntry(tk.Canvas):
    """Refined Liquid Glass Search Capsule with inset dark glass and focus ring glow."""

    def __init__(
        self,
        parent: tk.Widget,
        placeholder: str = "Search downloads...",
        on_change: Optional[Callable[[str], None]] = None,
        width: int = 220,
        height: int = 32,
        **kwargs,
    ):
        bg = kwargs.pop("bg", THEME["surface"])
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.entry_width = width
        self.entry_height = height
        self.placeholder = placeholder
        self.on_change = on_change
        self.is_focused = False

        self._draw_bg()

        # Inset search icon
        self.lbl_icon = tk.Label(self, text="⌕", font=(FONT_DISPLAY, 11, "bold"), bg=THEME["input_bg"], fg=THEME["text_secondary"])
        self.create_window(16, height // 2, window=self.lbl_icon)

        # Embedded text entry
        self.entry_var = tk.StringVar(self)
        self.entry = tk.Entry(
            self,
            textvariable=self.entry_var,
            bg=THEME["input_bg"],
            fg=THEME["text_secondary"],
            insertbackground=THEME["text_primary"],
            relief=tk.FLAT,
            font=FONT_BODY,
            bd=0,
        )
        self.entry.insert(0, placeholder)
        self.create_window(110, height // 2, window=self.entry, width=width - 60)

        # Clear button '✕'
        self.btn_clear = tk.Label(self, text="✕", font=(FONT_DISPLAY, 8), bg=THEME["input_bg"], fg=THEME["text_tertiary"], cursor="hand2")
        self.clear_win = self.create_window(width - 16, height // 2, window=self.btn_clear, state="hidden")

        self.btn_clear.bind("<Button-1>", lambda e: self.clear(), add="+")
        self.entry.bind("<FocusIn>", self._on_focus_in, add="+")
        self.entry.bind("<FocusOut>", self._on_focus_out, add="+")
        self.entry_var.trace_add("write", self._on_text_change)

    def _draw_bg(self):
        self.delete("glass_bg")
        border_col = THEME["focus_ring"] if self.is_focused else THEME["glass_border"]
        draw_liquid_glass_panel(
            self,
            1,
            1,
            self.entry_width - 1,
            self.entry_height - 1,
            r=RADIUS_MD,
            fill=THEME["input_bg"],
            border=border_col,
            rim_highlight="#2a3d5b" if not self.is_focused else THEME["focus_ring"],
            refraction=THEME["glass_refraction"],
            shadow=False,
            tags="glass_bg",
        )
        self.tag_lower("glass_bg")

    def _on_focus_in(self, e):
        self.is_focused = True
        self._draw_bg()
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=THEME["text_primary"])

    def _on_focus_out(self, e):
        self.is_focused = False
        self._draw_bg()
        if not self.entry.get().strip():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=THEME["text_secondary"])

    def _on_text_change(self, *args):
        txt = self.get().strip()
        if txt and txt != self.placeholder:
            self.itemconfigure(self.clear_win, state="normal")
        else:
            self.itemconfigure(self.clear_win, state="hidden")
        if self.on_change:
            self.on_change(txt)

    def clear(self):
        self.entry.delete(0, tk.END)
        self.itemconfigure(self.clear_win, state="hidden")
        if self.on_change:
            self.on_change("")

    def get(self) -> str:
        val = self.entry_var.get()
        return "" if val == self.placeholder else val


class AmbientMeshEngine:
    """Pre-rendered blurred ambient mesh engine for Liquid Glass interfaces.
    Uses coordinate translation at ~15 FPS with automatic 0 FPS sleep during idle / tray.
    """

    _instance: Optional["AmbientMeshEngine"] = None

    def __init__(self, width: int = 1600, height: int = 1200):
        self.width = width
        self.height = height
        self._mesh_img: Optional[Any] = None
        self._mesh_photo: Optional[Any] = None
        self._anim_id: Optional[str] = None
        self._t: float = 0.0
        self._is_running: bool = False
        self._last_interaction_time: float = time.time()
        self._idle_threshold_s: float = 5.0
        self._fps_delay_ms: int = 66  # ~15 FPS cap
        self.enabled: bool = True

    @classmethod
    def get_shared(cls) -> "AmbientMeshEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_mesh_image(self) -> Any:
        if self._mesh_img is None:
            from PIL import Image, ImageDraw, ImageFilter
            w, h = self.width, self.height
            bg = Image.new("RGB", (w, h), THEME["bg_dark"])
            d = ImageDraw.Draw(bg)
            # Sapphire glow upper-left
            d.ellipse([int(w * 0.08), -int(h * 0.15), int(w * 0.45), int(h * 0.45)], fill=THEME["mesh_sapphire"])
            # Prism violet glow lower-right
            d.ellipse([int(w * 0.55), int(h * 0.35), int(w * 1.05), int(h * 0.95)], fill=THEME["mesh_violet"])
            # Ocean teal glow center
            d.ellipse([int(w * 0.28), int(h * 0.22), int(w * 0.68), int(h * 0.72)], fill=THEME["mesh_teal"])
            self._mesh_img = bg.filter(ImageFilter.GaussianBlur(radius=80))
        return self._mesh_img

    def get_mesh_photo(self, master: Optional[tk.Misc] = None) -> Any:
        if self._mesh_photo is None:
            from PIL import ImageTk
            self._mesh_photo = ImageTk.PhotoImage(self.get_mesh_image(), master=master)
        return self._mesh_photo

    def notify_interaction(self):
        self._last_interaction_time = time.time()

    def start_animation(self, canvas: tk.Canvas, img_id: int):
        self._is_running = True
        self.notify_interaction()

        def _step():
            self._anim_id = None
            if not self._is_running or not canvas.winfo_exists():
                return

            if not self.enabled or is_reduced_motion():
                return

            try:
                top = canvas.winfo_toplevel()
                state = top.state()
                if state in ("withdrawn", "iconic"):
                    self._anim_id = canvas.after(2000, _step)
                    return
            except Exception:
                pass

            # Smart sleep when idle (>5s without interaction)
            if time.time() - self._last_interaction_time > self._idle_threshold_s:
                self._anim_id = canvas.after(1000, _step)
                return

            # 15 FPS organic drifting
            self._t += 0.035
            import math
            dx = -100 + int(35 * math.sin(self._t))
            dy = -100 + int(25 * math.cos(self._t * 0.7))
            try:
                canvas.coords(img_id, dx, dy)
            except Exception:
                pass

            self._anim_id = canvas.after(self._fps_delay_ms, _step)

        _step()

    def stop_animation(self, canvas: Optional[tk.Canvas] = None):
        self._is_running = False
        if self._anim_id is not None and canvas:
            try:
                canvas.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

