"""
UI/UX Pro Max - Design Tokens and Unified Theme for IDM Clone
High-precision dark utility theme inspired by Windows modern design and classic IDM.
"""

from typing import Callable, Optional
import tkinter as tk
from tkinter import ttk

# Cohesive Dark Precision Palette
THEME = {
    # Surfaces
    "bg_dark": "#18181b",         # Zinc-900: Main window background
    "surface": "#27272a",         # Zinc-800: Cards, dialogs, toolbars
    "surface_alt": "#202023",     # Slightly darker surface for containers
    "input_bg": "#141416",        # Deep background for text entries
    # Borders & Dividers
    "border": "#3f3f46",          # Zinc-700: Subtle boundary line
    "border_light": "#52525b",    # Zinc-600
    "focus_ring": "#38bdf8",      # Sky-400: Focus ring
    # Typography
    "text_primary": "#fafafa",    # Zinc-50: High contrast reading text
    "text_secondary": "#a1a1aa",  # Zinc-400: Muted labels and subtitles
    "text_disabled": "#71717a",   # Zinc-500: Disabled elements
    # Semantic Colors
    "accent_primary": "#0284c7",  # Sky-600: Primary action button
    "accent_hover": "#0369a1",    # Sky-700: Primary action hover
    "accent_active": "#075985",   # Sky-800: Primary active press
    "secondary_bg": "#3f3f46",    # Zinc-700: Secondary buttons
    "secondary_hover": "#52525b", # Zinc-600
    "success": "#10b981",         # Emerald-500: Success, complete, active speed
    "warning": "#f59e0b",         # Amber-500: Security warning
    "danger": "#ef4444",          # Rose-500: Delete, cancel, divider line
    "danger_hover": "#dc2626",
    # Component specifics
    "tree_bg": "#18181b",
    "tree_fg": "#f4f4f5",
    "tree_select": "#0369a1",
    "tree_heading_bg": "#27272a",
    "tree_heading_fg": "#ffffff",
    "progress_bg": "#141416",
    "progress_fill": "#0284c7",
    "progress_stripe": "#38bdf8",
    "part_divider": "#ef4444",
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


def create_modern_button(
    parent: tk.Widget,
    text: str,
    command: Optional[Callable] = None,
    kind: str = "secondary",  # 'primary', 'secondary', 'danger', 'toolbar'
    width: Optional[int] = None,
    padx: int = 12,
    pady: int = 4,
) -> tk.Button:
    """Creates a tactile, beautifully styled button with active hover animations."""
    if kind == "primary":
        bg_normal = THEME["accent_primary"]
        bg_hover = THEME["accent_hover"]
        bg_active = THEME["accent_active"]
        fg = THEME["text_primary"]
        font = FONT_HEADING
    elif kind == "danger":
        bg_normal = THEME["danger"]
        bg_hover = THEME["danger_hover"]
        bg_active = "#b91c1c"
        fg = THEME["text_primary"]
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
        bg_active = "#27272a"
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
        rowheight=26,
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
