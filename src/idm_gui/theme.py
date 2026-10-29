"""
UI/UX Pro Max - Design Tokens and Unified Theme for IDM Clone
High-precision dark utility theme inspired by Windows modern design and classic IDM.
"""

from typing import Callable, Optional
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
    # Typography (Cool Slate Ramp)
    "text_primary": "#f1f5f9",     # Slate-50: Luminous crisp text (no halation)
    "text_secondary": "#94a3b8",   # Slate-400: High-contrast cool secondary labels (WCAG AAA)
    "text_tertiary": "#7d8da1",    # Slate-400/500: Captions & metadata (5.48:1 WCAG AA)
    "text_disabled": "#526075",    # Slate-600: Disabled / coming soon text
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
    "tree_fg": "#f1f5f9",
    "tree_select": "#2563eb",
    "tree_heading_bg": "#1b2230",
    "tree_heading_fg": "#f1f5f9",
    "progress_bg": "#0f131d",
    "progress_fill": "#2563eb",
    "progress_stripe": "#60a5fa",
    "part_divider": "#e11d48",
}

FONT_DISPLAY = "SF Pro Display"
FONT_FAMILY = "SF Pro Text"
FONT_TITLE = (FONT_DISPLAY, 11, "bold")
FONT_HEADING = (FONT_DISPLAY, 9, "bold")
FONT_BODY = (FONT_FAMILY, 9)
FONT_SMALL = (FONT_FAMILY, 8)
FONT_CODE = ("Consolas", 9)


def apply_theme_to_toplevel(top: tk.Toplevel, width: int, height: int, title: str):
    """Sets standard background, icon, and centered geometry for a modal or dialog."""
    top.title(title)
    top.geometry(f"{width}x{height}")
    top.resizable(False, False)
    top.configure(bg=THEME["surface"])

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


def draw_round_rectangle(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, r: int = 8, fill: str = "", outline: str = "", width: int = 1):
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
    return canvas.create_polygon(points, fill=fill, outline=outline, width=width, smooth=True)


class RoundedButton(tk.Canvas):
    """Tactile rounded button built on Tkinter Canvas with smooth hover transitions."""

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
            self.fg = "#ffffff"
            self.font = FONT_HEADING
        elif kind == "danger":
            self.bg_normal = THEME["danger"]
            self.bg_hover = THEME["danger_hover"]
            self.bg_active = "#8b0000"
            self.fg = "#ffffff"
            self.font = FONT_BODY
        elif kind == "toolbar":
            self.bg_normal = THEME["surface"]
            self.bg_hover = THEME["secondary_hover"]
            self.bg_active = THEME["accent_primary"]
            self.fg = THEME["text_primary"]
            self.font = FONT_BODY
        else:  # secondary
            self.bg_normal = THEME["secondary_bg"]
            self.bg_hover = THEME["secondary_hover"]
            self.bg_active = "#2c2c2e"
            self.fg = THEME["text_primary"]
            self.font = FONT_BODY

        try:
            font_obj = tkfont.Font(font=self.font)
            self.text_w = font_obj.measure(self.text)
            self.text_h = font_obj.metrics("linespace")
        except Exception:
            self.text_w = max(40, len(self.text) * 8)
            self.text_h = 18
        self.total_w = self.custom_width if self.custom_width else (self.text_w + (self.padx * 2))
        self.total_h = self.text_h + (self.pady * 2)

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

    def _draw(self, fill_color):
        self.delete("all")
        draw_round_rectangle(self, 0, 0, self.total_w, self.total_h, r=self.radius, fill=fill_color)
        self.create_text(self.total_w // 2, self.total_h // 2, text=self.text, fill=self.fg, font=self.font)

    def _on_enter(self, e):
        if self.state != "disabled":
            self._draw(self.bg_hover)

    def _on_leave(self, e):
        if self.state != "disabled":
            self._draw(self.bg_normal)

    def _on_press(self, e):
        if self.state != "disabled":
            self._draw(self.bg_active)

    def _on_release(self, e):
        if self.state != "disabled":
            self._draw(self.bg_hover)
            if self.command:
                self.command()

    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
            try:
                font_obj = tkfont.Font(font=self.font)
                self.text_w = font_obj.measure(self.text)
            except Exception:
                self.text_w = max(40, len(self.text) * 8)
            self.total_w = self.custom_width if self.custom_width else (self.text_w + (self.padx * 2))
            super().config(width=self.total_w)
            self._draw(self.bg_normal)
        if "state" in kwargs:
            self.state = kwargs["state"]
            self.config(cursor="hand2" if self.state != "disabled" else "arrow")
        if "command" in kwargs:
            self.command = kwargs["command"]
        canvas_kwargs = {k: v for k, v in kwargs.items() if k not in ("text", "state", "command")}
        if canvas_kwargs:
            super().config(**canvas_kwargs)

    def cget(self, key):
        if key == "text":
            return self.text
        if key == "state":
            return self.state
        if key == "command":
            return self.command
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
    )
    style.map(
        "Treeview",
        background=[("selected", THEME["tree_select"])],
        foreground=[("selected", "#ffffff")],
    )

    # Treeview Headings
    style.configure(
        "Treeview.Heading",
        background=THEME["tree_heading_bg"],
        foreground=THEME["tree_heading_fg"],
        font=FONT_HEADING,
        relief="flat",
        padding=[6, 4],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", THEME["secondary_hover"])],
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
