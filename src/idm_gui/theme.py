"""
UI/UX Pro Max - Design Tokens and Unified Theme for IDM Clone
High-precision dark utility theme inspired by Windows modern design and classic IDM.
"""

from typing import Callable, Optional
import tkinter as tk
from tkinter import ttk

# Cohesive Dark Precision Palette (Apple-inspired Dark Minimalist)
THEME = {
    # Surfaces
    "bg_dark": "#1c1c1e",          # Apple System Gray 6: Window background
    "surface": "#2c2c2e",          # Apple System Gray 5: Toolbar, cards, dialogs
    "surface_alt": "#242426",      # Apple Sidebar surface
    "surface_canvas": "#121214",   # Deepest canvas for table
    "input_bg": "#141416",         # Deep background for text entries
    # Borders & Dividers
    "border": "#3a3a3c",           # Apple System Gray 4: Subtle boundary line
    "border_light": "#48484a",     # Muted divider
    "focus_ring": "#0071e3",       # Apple System Azure: Focus ring
    # Typography
    "text_primary": "#f5f5f7",     # Apple high-contrast text (no halation)
    "text_secondary": "#c7c7cc",   # High-contrast secondary labels (WCAG AAA)
    "text_tertiary": "#aeaeb2",    # Captions & status text (WCAG AA)
    "text_disabled": "#8e8e93",    # Disabled / coming soon text (WCAG AA)
    # Semantic Colors (Single Accent)
    "accent_primary": "#0071e3",   # Apple Refined Azure: 4.70:1 with white
    "accent_hover": "#0062c4",     # 5.93:1 with white
    "accent_active": "#005bb5",    # 6.64:1 with white
    "secondary_bg": "#3a3a3c",     # Secondary buttons
    "secondary_hover": "#48484a",
    "success": "#10b981",          # Emerald-500: Active speed / complete
    "warning": "#f59e0b",          # Amber-500: Security warning
    "danger": "#d32f2f",           # Apple Destructive Red: 4.98:1 with white
    "danger_hover": "#b91c1c",     # 6.47:1 with white
    "danger_text": "#ff6358",      # 4.76:1 on #2c2c2e
    # Component specifics
    "tree_bg": "#121214",
    "tree_fg": "#f5f5f7",
    "tree_select": "#0071e3",
    "tree_heading_bg": "#2c2c2e",
    "tree_heading_fg": "#f5f5f7",
    "progress_bg": "#1c1c1e",
    "progress_fill": "#0071e3",
    "progress_stripe": "#38bdf8",
    "part_divider": "#d32f2f",
}

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 10, "bold")
FONT_HEADING = (FONT_FAMILY, 9, "bold")
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


def create_modern_button(
    parent: tk.Widget,
    text: str,
    command: Optional[Callable] = None,
    kind: str = "secondary",  # 'primary', 'secondary', 'danger', 'toolbar'
    width: Optional[int] = None,
    padx: int = 12,
    pady: int = 4,
    tooltip: Optional[str] = None,
) -> tk.Button:
    """Creates a tactile, beautifully styled button with active hover animations."""
    if kind == "primary":
        bg_normal = THEME["accent_primary"]
        bg_hover = THEME["accent_hover"]
        bg_active = THEME["accent_active"]
        fg = "#ffffff"
        font = FONT_HEADING
    elif kind == "danger":
        bg_normal = THEME["danger"]
        bg_hover = THEME["danger_hover"]
        bg_active = "#8b0000"
        fg = "#ffffff"
        font = FONT_BODY
    elif kind == "toolbar":
        bg_normal = THEME["surface"]
        bg_hover = THEME["secondary_hover"]
        bg_active = THEME["accent_primary"]
        fg = THEME["text_primary"]
        font = FONT_BODY
    else:  # secondary
        bg_normal = THEME["secondary_bg"]
        bg_hover = THEME["secondary_hover"]
        bg_active = "#2c2c2e"
        fg = THEME["text_primary"]
        font = FONT_BODY

    btn = tk.Button(
        parent,
        text=text,
        bg=bg_normal,
        fg=fg,
        activebackground=bg_active,
        activeforeground=fg,
        font=font,
        relief=tk.FLAT,
        bd=0,
        padx=padx,
        pady=pady,
        cursor="hand2",
    )
    if command is not None:
        btn.config(command=command)
    if width:
        btn.config(width=width)

    # Hover animations (interactive state transition)
    def on_enter(e):
        if btn.cget("state") != "disabled":
            btn.config(bg=bg_hover)

    def on_leave(e):
        if btn.cget("state") != "disabled":
            btn.config(bg=bg_normal)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    if tooltip:
        Tooltip(btn, tooltip)

    return btn


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
    )
