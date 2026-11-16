"""Modern Liquid Glass Virtualized Table Component for Just Press Download.
Replaces ttk.Treeview with a high-performance Canvas-based virtualized table.
Features:
- Crisp white typography for filenames (#ffffff)
- Right-aligned metrics for size and speed (#cbd5e1)
- Dimmed URL (#7c8ba1) with ellipsis and hover tooltip
- Smooth rounded pill progress bars with animated gradient shimmer waves
- Modern Liquid Glass empty state
- Full keyboard navigation (Up, Down, Enter, Delete, Ctrl+A) and multi-select (Ctrl/Shift+Click)
- 100% API compatibility with ttk.Treeview for seamless drop-in integration.
"""

import math
import os
import time
from typing import Any, Callable, Optional, Sequence
import tkinter as tk
import tkinter.font as tkfont

from idm_gui.theme import (
    THEME,
    FONT_DISPLAY,
    FONT_FAMILY,
    FONT_HEADING,
    FONT_BODY,
    FONT_SMALL,
    FONT_CODE,
    RADIUS_XS,
    RADIUS_SM,
    RADIUS_MD,
    RADIUS_LG,
    AmbientMeshEngine,
    draw_liquid_glass_panel,
    draw_round_rectangle,
    interpolate_color,
    is_reduced_motion,
    scale_px,
    GlassThinScrollbar,
    Tooltip,
)
from idm_gui.i18n import tr


class GlassTableView(tk.Frame):
    """Virtualized Liquid Glass Table View matching ttk.Treeview API contract."""

    def __init__(
        self,
        parent: tk.Widget,
        columns: Sequence[str] = ("name", "size", "status", "progress", "speed", "url"),
        row_height: int = 42,
        on_add_url_click: Optional[Callable] = None,
        **kwargs,
    ):
        bg = kwargs.pop("bg", THEME["tree_bg"])  # Match TactileTableContainer.inner_frame
        super().__init__(parent, bg=bg, **kwargs)

        self.columns_keys = list(columns)
        self.row_height = row_height
        self.on_add_url_click = on_add_url_click

        # Column configuration: width, minwidth, anchor, title, command
        self._col_config: dict[str, dict[str, Any]] = {}
        defaults = {
            "name": {"width": 240, "minwidth": 140, "anchor": tk.W, "title": "Nama Berkas"},
            "size": {"width": 85, "minwidth": 70, "anchor": tk.E, "title": "Ukuran"},
            "status": {"width": 130, "minwidth": 110, "anchor": tk.W, "title": "Status"},
            "progress": {"width": 135, "minwidth": 110, "anchor": tk.W, "title": "Progres"},
            "speed": {"width": 105, "minwidth": 85, "anchor": tk.E, "title": "Kecepatan"},
            "url": {"width": 260, "minwidth": 120, "anchor": tk.W, "title": "URL Unduhan"},
        }
        for k in self.columns_keys:
            self._col_config[k] = defaults.get(k, {"width": 120, "minwidth": 80, "anchor": tk.W, "title": k.title()})

        # Table data store: list of row IDs in display order, and dict of row data
        self._items: list[str] = []
        self._data: dict[str, dict[str, Any]] = {}
        self._selected_ids: set[str] = set()
        self._anchor_id: Optional[str] = None
        self._hover_id: Optional[str] = None
        self._hover_url: Optional[str] = None

        # Scrolling state
        self._scroll_offset_y: int = 0
        self._shimmer_phase: float = 0.0
        self._shimmer_timer_id: Optional[str] = None

        # Coalesced rendering: batch rapid item()/insert() updates into ONE viewport render
        self._render_scheduled: bool = False
        self._header_glass_photo: Optional[Any] = None
        self._header_glass_key: Optional[tuple[int, int, int, int]] = None
        self._viewport_glass_photo: Optional[Any] = None
        self._viewport_glass_key: Optional[tuple[int, int, int, int]] = None
        self._empty_card_photo: Optional[Any] = None
        self._empty_card_key: Optional[tuple[int, int, int, int]] = None
        self._empty_btn_bounds: Optional[tuple[int, int, int, int]] = None

        # Event callbacks registered via bind()
        self._custom_bindings: dict[str, list[Callable]] = {}

        # 1. Header Bar Canvas (Height: 32px)
        self.header_canvas = tk.Canvas(
            self,
            height=32,
            bg=THEME["tree_bg"],   # Match container's fallback background
            highlightthickness=0,
            bd=0,
        )
        self.header_canvas.pack(side=tk.TOP, fill=tk.X)

        # 2. Body Viewport Frame (Holds Viewport Canvas + GlassThinScrollbar)
        self.body_frame = tk.Frame(self, bg=THEME["tree_bg"])  # Match container
        self.body_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.viewport = tk.Canvas(
            self.body_frame,
            bg=THEME["tree_bg"],   # Match container; container glass shows through
            highlightthickness=0,
            bd=0,
            takefocus=True,
        )
        self.viewport.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = GlassThinScrollbar(
            self.body_frame,
            command=self._on_scrollbar_move,
            width=8,
            bg=THEME["tree_bg"],  # Match container
            glass_backdrop=True,
            tint_rgba=(8, 12, 20, 165),
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tooltip for URL hover
        self._url_tooltip_win: Optional[tk.Toplevel] = None

        # Bindings for mouse & keyboard
        self._setup_events()

        # Start background shimmer wave loop
        self._schedule_shimmer()

    # =========================================================================
    # EVENT HANDLING & KEYBOARD NAVIGATION
    # =========================================================================

    def _setup_events(self):
        self.bind("<Configure>", self._on_resize, add="+")
        self.viewport.bind("<Configure>", self._on_resize, add="+")
        self.header_canvas.bind("<Configure>", self._redraw_header, add="+")

        # Viewport mouse navigation
        self.viewport.bind("<Button-1>", self._on_click, add="+")
        self.viewport.bind("<Control-Button-1>", self._on_ctrl_click, add="+")
        self.viewport.bind("<Shift-Button-1>", self._on_shift_click, add="+")
        self.viewport.bind("<Double-Button-1>", self._on_double_click, add="+")
        self.viewport.bind("<Button-3>", self._on_right_click, add="+")
        self.viewport.bind("<Motion>", self._on_mouse_move, add="+")
        self.viewport.bind("<Leave>", self._on_mouse_leave, add="+")

        # Mouse wheel scrolling
        self.viewport.bind("<MouseWheel>", self._on_mouse_wheel, add="+")
        self.viewport.bind("<Button-4>", lambda e: self._scroll_by_units(-3), add="+")
        self.viewport.bind("<Button-5>", lambda e: self._scroll_by_units(3), add="+")

        # Keyboard navigation
        self.viewport.bind("<Up>", self._on_key_up, add="+")
        self.viewport.bind("<Down>", self._on_key_down, add="+")
        self.viewport.bind("<Home>", self._on_key_home, add="+")
        self.viewport.bind("<End>", self._on_key_end, add="+")
        self.viewport.bind("<Control-a>", self._on_key_select_all, add="+")
        self.viewport.bind("<Control-A>", self._on_key_select_all, add="+")
        self.viewport.bind("<Delete>", self._on_key_delete, add="+")
        self.viewport.bind("<Return>", self._on_key_return, add="+")

        # Header sorting clicks
        self.header_canvas.bind("<Button-1>", self._on_header_click, add="+")

    def _on_resize(self, event=None):
        self._responsive_fit_columns()
        self._update_scroll_bounds()
        self._redraw_header()
        self._render_viewport()

    def _responsive_fit_columns(self):
        """Dynamically fit all 6 columns to the available viewport width so Speed & URL
        are always visible (or gracefully narrow) without clipping."""
        try:
            vw = self.viewport.winfo_width()
            vh = self.viewport.winfo_height()
        except Exception:
            return
        if vw < 320:
            return

        fixed_cols = ["size", "status", "progress", "speed"]
        fixed_total = sum(self._col_config[k]["width"] for k in fixed_cols)
        remaining = max(0, vw - fixed_total - 16)

        name_w = self._col_config["name"]["width"]
        url_w = self._col_config["url"]["width"]

        if remaining >= (name_w + url_w):
            # Room to expand: distribute proportionally between name and url
            expand = remaining - (name_w + url_w)
            self._col_config["name"]["width"] = name_w + int(expand * 0.4)
            self._col_config["url"]["width"] = url_w + int(expand * 0.6)
        else:
            # Tight space: shrink name and url to fit
            if remaining > 220:
                self._col_config["name"]["width"] = max(120, int(remaining * 0.45))
                self._col_config["url"]["width"] = max(100, remaining - self._col_config["name"]["width"])
            else:
                # Very compact: hide URL by minimising it, shrink name
                self._col_config["name"]["width"] = max(110, int(remaining * 0.6))
                self._col_config["url"]["width"] = max(80, remaining - self._col_config["name"]["width"])

    def _on_mouse_wheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self._scroll_by_units(delta * 2)

    def _scroll_by_units(self, units: int):
        total_h = len(self._items) * self.row_height
        vh = self.viewport.winfo_height()
        max_scroll = max(0, total_h - vh)
        self._scroll_offset_y = max(0, min(max_scroll, self._scroll_offset_y + (units * self.row_height)))
        self._update_scroll_bounds()
        self._render_viewport()

    def _on_scrollbar_move(self, action: str, frac_str: str):
        total_h = len(self._items) * self.row_height
        vh = self.viewport.winfo_height()
        max_scroll = max(0, total_h - vh)
        if max_scroll > 0:
            frac = float(frac_str)
            self._scroll_offset_y = int(frac * max_scroll)
            self._render_viewport()
            self._update_scroll_bounds()

    def _update_scroll_bounds(self):
        total_h = len(self._items) * self.row_height
        vh = self.viewport.winfo_height()
        if total_h <= 0 or vh <= 0:
            self.scrollbar.set(0.0, 1.0)
            return
        first = self._scroll_offset_y / total_h
        last = min(1.0, (self._scroll_offset_y + vh) / total_h)
        self.scrollbar.set(first, last)

    def _get_row_at_y(self, y: int) -> Optional[str]:
        effective_y = y + self._scroll_offset_y
        row_idx = effective_y // self.row_height
        if 0 <= row_idx < len(self._items):
            return self._items[row_idx]
        return None

    def _on_click(self, event):
        self.viewport.focus_set()
        if not self._items:
            # Check if clicked on empty state "+ Add URL" button
            if self._empty_btn_bounds:
                bx1, by1, bx2, by2 = self._empty_btn_bounds
            else:
                vw = self.viewport.winfo_width()
                vh = self.viewport.winfo_height()
                cx = vw // 2
                cy = vh // 2
                bx1, by1, bx2, by2 = cx - 90, cy + 42, cx + 90, cy + 72
            if bx1 <= event.x <= bx2 and by1 <= event.y <= by2:
                if self.on_add_url_click:
                    self.on_add_url_click()
            return

        row_id = self._get_row_at_y(event.y)
        if row_id:
            self._selected_ids = {row_id}
            self._anchor_id = row_id
        else:
            self._selected_ids.clear()
            self._anchor_id = None
        self._schedule_coalesced_render()
        self._trigger_custom_binding("<<TreeviewSelect>>", event)

    def _on_ctrl_click(self, event):
        self.viewport.focus_set()
        row_id = self._get_row_at_y(event.y)
        if row_id:
            if row_id in self._selected_ids:
                self._selected_ids.remove(row_id)
            else:
                self._selected_ids.add(row_id)
            self._anchor_id = row_id
        self._schedule_coalesced_render()
        self._trigger_custom_binding("<<TreeviewSelect>>", event)

    def _on_shift_click(self, event):
        self.viewport.focus_set()
        row_id = self._get_row_at_y(event.y)
        if row_id and self._anchor_id and self._anchor_id in self._items:
            idx1 = self._items.index(self._anchor_id)
            idx2 = self._items.index(row_id)
            start_i = min(idx1, idx2)
            end_i = max(idx1, idx2)
            self._selected_ids = set(self._items[start_i : end_i + 1])
        elif row_id:
            self._selected_ids = {row_id}
            self._anchor_id = row_id
        self._schedule_coalesced_render()
        self._trigger_custom_binding("<<TreeviewSelect>>", event)

    def _on_double_click(self, event):
        row_id = self._get_row_at_y(event.y)
        if row_id:
            self._selected_ids = {row_id}
            self._anchor_id = row_id
            self._schedule_coalesced_render()
            self._trigger_custom_binding("<Double-1>", event)

    def _on_right_click(self, event):
        self.viewport.focus_set()
        row_id = self._get_row_at_y(event.y)
        if row_id and row_id not in self._selected_ids:
            self._selected_ids = {row_id}
            self._anchor_id = row_id
            self._render_viewport()
        self._trigger_custom_binding("<Button-3>", event)

    def _on_key_up(self, event):
        if not self._items:
            return "break"
        if not self._selected_ids:
            new_id = self._items[0]
        else:
            cur_id = self._anchor_id or list(self._selected_ids)[0]
            cur_idx = self._items.index(cur_id) if cur_id in self._items else 0
            new_idx = max(0, cur_idx - 1)
            new_id = self._items[new_idx]
        self._selected_ids = {new_id}
        self._anchor_id = new_id
        self._scroll_into_view(new_id)
        self._render_viewport()
        self._trigger_custom_binding("<<TreeviewSelect>>", event)
        return "break"

    def _on_key_down(self, event):
        if not self._items:
            return "break"
        if not self._selected_ids:
            new_id = self._items[0]
        else:
            cur_id = self._anchor_id or list(self._selected_ids)[0]
            cur_idx = self._items.index(cur_id) if cur_id in self._items else 0
            new_idx = min(len(self._items) - 1, cur_idx + 1)
            new_id = self._items[new_idx]
        self._selected_ids = {new_id}
        self._anchor_id = new_id
        self._scroll_into_view(new_id)
        self._render_viewport()
        self._trigger_custom_binding("<<TreeviewSelect>>", event)
        return "break"

    def _on_key_home(self, event):
        if self._items:
            new_id = self._items[0]
            self._selected_ids = {new_id}
            self._anchor_id = new_id
            self._scroll_into_view(new_id)
            self._render_viewport()
            self._trigger_custom_binding("<<TreeviewSelect>>", event)
        return "break"

    def _on_key_end(self, event):
        if self._items:
            new_id = self._items[-1]
            self._selected_ids = {new_id}
            self._anchor_id = new_id
            self._scroll_into_view(new_id)
            self._render_viewport()
            self._trigger_custom_binding("<<TreeviewSelect>>", event)
        return "break"

    def _on_key_select_all(self, event):
        self._selected_ids = set(self._items)
        self._render_viewport()
        self._trigger_custom_binding("<<TreeviewSelect>>", event)
        return "break"

    def _on_key_delete(self, event):
        # Trigger Delete on parent if bound or let binding handle it
        self._trigger_custom_binding("<Delete>", event)
        return "break"

    def _on_key_return(self, event):
        self._trigger_custom_binding("<Double-1>", event)
        return "break"

    def _scroll_into_view(self, row_id: str):
        if row_id not in self._items:
            return
        idx = self._items.index(row_id)
        row_top = idx * self.row_height
        row_bot = row_top + self.row_height
        vh = self.viewport.winfo_height()

        if row_top < self._scroll_offset_y:
            self._scroll_offset_y = row_top
        elif row_bot > self._scroll_offset_y + vh:
            self._scroll_offset_y = row_bot - vh
        self._update_scroll_bounds()

    def _on_mouse_move(self, event):
        if not self._items:
            if self._empty_btn_bounds:
                bx1, by1, bx2, by2 = self._empty_btn_bounds
                over_btn = bx1 <= event.x <= bx2 and by1 <= event.y <= by2
                self.viewport.configure(cursor="hand2" if over_btn else "")
            return

        self.viewport.configure(cursor="")
        row_id = self._get_row_at_y(event.y)
        if row_id != self._hover_id:
            self._hover_id = row_id
            self._schedule_coalesced_render()

        # Check if hovering over URL column
        if row_id and row_id in self._data:
            vals = self._data[row_id].get("values", [])
            if len(vals) >= 6:
                url = str(vals[5])
                url_x_start = sum(self._col_config[k]["width"] for k in self.columns_keys[:5])
                if event.x >= url_x_start:
                    self._show_url_tooltip(event.x_root, event.y_root, url)
                    return
        self._hide_url_tooltip()

    def _on_mouse_leave(self, event):
        self.viewport.configure(cursor="")
        if self._hover_id is not None:
            self._hover_id = None
            self._schedule_coalesced_render()
        self._hide_url_tooltip()

    def _show_url_tooltip(self, rx: int, ry: int, url: str):
        if not url:
            self._hide_url_tooltip()
            return
        if self._hover_url == url and self._url_tooltip_win:
            return
        self._hide_url_tooltip()
        self._hover_url = url

        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(bg=THEME["surface"], padx=8, pady=4)

        lbl = tk.Label(
            tip,
            text=url,
            bg=THEME["surface"],
            fg=THEME["text_primary"],
            font=FONT_SMALL,
            wraplength=400,
            justify=tk.LEFT,
        )
        lbl.pack()
        tip.geometry(f"+{rx + 12}+{ry + 16}")
        self._url_tooltip_win = tip

    def _hide_url_tooltip(self):
        if self._url_tooltip_win:
            try:
                self._url_tooltip_win.destroy()
            except Exception:
                pass
            self._url_tooltip_win = None
        self._hover_url = None

    def _on_header_click(self, event):
        cur_x = 0
        for k in self.columns_keys:
            w = self._col_config[k]["width"]
            if cur_x <= event.x < cur_x + w:
                cmd = self._col_config[k].get("command")
                if cmd:
                    cmd()
                break
            cur_x += w

    # =========================================================================
    # RENDERING ENGINE (VIRTUALIZED VIEWPORT & HEADER)
    # =========================================================================

    def _redraw_header(self, event=None):
        self.header_canvas.delete("all")
        hw = self.header_canvas.winfo_width()
        hh = 32

        # Header background: coordinate-aligned glass backdrop matching TactileTableContainer
        drew_glass = False
        if hw >= 10:
            try:
                top_w = self.header_canvas.winfo_toplevel()
                rx = max(0, self.header_canvas.winfo_rootx() - top_w.winfo_rootx())
                ry = max(0, self.header_canvas.winfo_rooty() - top_w.winfo_rooty())
                key = (hw, hh, rx, ry)
                if key != self._header_glass_key or self._header_glass_photo is None:
                    self._header_glass_photo = AmbientMeshEngine.get_shared().create_glass_backdrop(
                        w=hw,
                        h=hh,
                        root_x=rx,
                        root_y=ry,
                        tint_rgba=(8, 12, 20, 165),
                    )
                    self._header_glass_key = key
                self.header_canvas.create_image(0, 0, image=self._header_glass_photo, anchor=tk.NW)
                drew_glass = True
            except Exception:
                drew_glass = False

        if not drew_glass:
            self.header_canvas.create_rectangle(0, 0, hw, hh, fill=THEME["tree_bg"], outline="")

        # Specular bottom hairline inset cleanly inside container
        self.header_canvas.create_line(4, hh - 1, max(4, hw - 4), hh - 1, fill=THEME["glass_border"], width=1)

        cur_x = 0
        for k in self.columns_keys:
            conf = self._col_config[k]
            cw = conf["width"]
            title = conf.get("title", k.title())
            anchor = conf.get("anchor", tk.W)

            tx = cur_x + 14 if anchor == tk.W else (cur_x + cw - 14 if anchor == tk.E else cur_x + (cw // 2))
            t_anchor = anchor

            self.header_canvas.create_text(
                tx,
                hh // 2,
                text=title.upper(),
                fill=THEME["text_tertiary"],
                font=(FONT_DISPLAY, 8, "bold"),
                anchor=t_anchor,
            )

            # Hairline vertical column divider
            if cur_x + cw < hw:
                self.header_canvas.create_line(cur_x + cw, 6, cur_x + cw, hh - 6, fill=THEME["border"], width=1)
            cur_x += cw

    def _schedule_coalesced_render(self):
        """Coalesce bursts of insert()/item() calls into a single viewport render.

        Without this, _tick_ui updating N rows triggers N full viewport renders
        per tick, each with per-character font.measure round-trips.
        """
        if self._render_scheduled:
            return
        self._render_scheduled = True
        self.viewport.after_idle(self._coalesced_render)

    def _coalesced_render(self):
        self._render_scheduled = False
        self._render_viewport()

    def _render_viewport(self):
        self.viewport.delete("row_item")
        self.viewport.delete("empty_state")

        vh = self.viewport.winfo_height()
        vw = self.viewport.winfo_width()

        # 0. Translucent Liquid Glass Mesh Background behind all rows
        self._ensure_viewport_glass_photo(vw, vh)

        # Check Empty State
        if not self._items:
            self._render_empty_state(vw, vh)
            return

        self._empty_btn_bounds = None
        total_rows = len(self._items)
        start_idx = max(0, self._scroll_offset_y // self.row_height)
        end_idx = min(total_rows, (self._scroll_offset_y + vh) // self.row_height + 1)

        for idx in range(start_idx, end_idx):
            item_id = self._items[idx]
            y = (idx * self.row_height) - self._scroll_offset_y
            self._render_row(item_id, idx, y, vw)

    def _ensure_viewport_glass_photo(self, vw: int, vh: int):
        """Renders a coordinate-aligned Liquid Glass mesh backdrop behind table rows
        and empty state so the interior blends seamlessly with TactileTableContainer."""
        if vw < 10 or vh < 10:
            return
        try:
            top_w = self.viewport.winfo_toplevel()
            rx = max(0, self.viewport.winfo_rootx() - top_w.winfo_rootx())
            ry = max(0, self.viewport.winfo_rooty() - top_w.winfo_rooty())
            key = (vw, vh, rx, ry)
            if key != self._viewport_glass_key or self._viewport_glass_photo is None:
                self._viewport_glass_photo = AmbientMeshEngine.get_shared().create_glass_backdrop(
                    w=vw,
                    h=vh,
                    root_x=rx,
                    root_y=ry,
                    tint_rgba=(8, 12, 20, 165),
                )
                self._viewport_glass_key = key
                self.viewport.delete("bg_mesh")
                self.viewport.create_image(0, 0, image=self._viewport_glass_photo, anchor=tk.NW, tags="bg_mesh")
            self.viewport.tag_lower("bg_mesh")
        except Exception:
            pass

    def _render_row(self, item_id: str, row_idx: int, y: int, vw: int):
        data = self._data.get(item_id, {})
        values = data.get("values", [])
        tags = data.get("tags", ())
        is_selected = item_id in self._selected_ids
        is_hovered = item_id == self._hover_id
        rh = self.row_height

        # 1. Row Background: Selected Glass / Hover Frosted / Alternating Subtle
        if is_selected:
            # Luminous glass selected row: stipple dithering for container glass glow-through
            self.viewport.create_rectangle(4, y + 2, vw - 4, y + rh - 2, fill="#1e4a7a", outline=THEME["accent_primary"], stipple="gray75", tags="row_item")
            # Left cyan active indicator pip
            self.viewport.create_rectangle(4, y + 6, 7, y + rh - 6, fill=THEME["accent_glow"], outline="", tags="row_item")
        elif is_hovered:
            # Frosted glass hover highlight: stipple dithering for container glass glow-through
            self.viewport.create_rectangle(4, y + 2, vw - 4, y + rh - 2, fill="#2a4064", outline=THEME["glass_border"], stipple="gray50", tags="row_item")
        else:
            is_even = row_idx % 2 == 0
            # Semi-transparent look via stipple dithering (Tk has no per-item alpha);
            # lets the container glass panel glow through while keeping text contrast.
            # Use theme-based colors that work with the TactileTableContainer glass (tree_bg base)
            bg_col = "#182338" if is_even else "#0f1626"  # Slightly darker, works with container glass
            self.viewport.create_rectangle(4, y + 2, vw - 4, y + rh - 2, fill=bg_col, outline="", stipple="gray50", tags="row_item")

        # 2. Extract Values
        fn = str(values[0]) if len(values) > 0 else ""
        size_str = str(values[1]) if len(values) > 1 else ""
        status_str = str(values[2]) if len(values) > 2 else ""
        prog_val = str(values[3]) if len(values) > 3 else ""
        speed_str = str(values[4]) if len(values) > 4 else ""
        url_str = str(values[5]) if len(values) > 5 else ""

        # Compute exact left and right bounds for each column from 0:
        col_x = {}
        cur_x = 0
        for k in self.columns_keys:
            col_x[k] = cur_x
            cur_x += self._col_config[k]["width"]

        mid_y = y + (rh // 2)

        # 3. Col 0: File Name (Consistent Category Emoji Icon + Pure White Bold Text)
        name_x = col_x["name"] + 14
        # Strip legacy double icon prefix (e.g. "📁 name.zip") so only ONE consistent icon is shown
        import re
        fn_clean = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF]\s+", "", fn).strip()
        icon = self._get_file_icon(fn_clean)
        self.viewport.create_text(name_x, mid_y, text=icon, font=(FONT_DISPLAY, 11), fill=THEME["accent_glow"], anchor=tk.W, tags="row_item")

        # Ellipsize file name if exceeds column width
        avail_name_w = self._col_config["name"]["width"] - 48
        disp_name = self._fit_text_with_ellipsis(fn_clean, avail_name_w, (FONT_DISPLAY, 9, "bold"))
        # File name text always starts at the exact same fixed X position (name_x + 24)
        self.viewport.create_text(name_x + 24, mid_y, text=disp_name, font=(FONT_DISPLAY, 9, "bold"), fill=THEME["text_primary"], anchor=tk.W, tags="row_item")

        # 4. Col 1: Size (Right-aligned cool slate under SIZE header)
        size_right_x = col_x["size"] + self._col_config["size"]["width"] - 14
        self.viewport.create_text(size_right_x, mid_y, text=size_str, font=("Consolas", 9), fill=THEME["text_secondary"], anchor=tk.E, tags="row_item")

        # 5. Col 2: Status (Dot + Semantic Colored Text under STATUS header)
        status_left_x = col_x["status"] + 14
        st_dot, st_color = self._get_status_style(status_str, tags)
        self.viewport.create_text(status_left_x, mid_y, text="●", font=(FONT_DISPLAY, 7, "bold"), fill=st_color, anchor=tk.W, tags="row_item")
        clean_status = status_str.replace("⚡ ", "").replace("✓ ", "").replace("⏸ ", "").replace("❌ ", "").strip()
        self.viewport.create_text(status_left_x + 12, mid_y, text=clean_status, font=(FONT_DISPLAY, 8, "bold"), fill=st_color, anchor=tk.W, tags="row_item")

        # 6. Col 3: Progress Bar Pill + Shimmer Wave + Percent (under PROGRESS header)
        prog_left_x = col_x["progress"] + 14
        pct_float, pct_text = self._parse_progress(prog_val)
        bar_w = 64
        bar_h = 7
        bx = prog_left_x
        by = mid_y - (bar_h // 2)

        # Trough capsule
        draw_round_rectangle(self.viewport, bx, by, bx + bar_w, by + bar_h, r=3, fill="#0c1422", outline="#1a273c", width=1, tags="row_item")

        # Progress Fill
        fill_w = max(0, min(bar_w, int(bar_w * pct_float)))
        if fill_w > 0:
            fill_col = st_color
            draw_round_rectangle(self.viewport, bx, by, bx + fill_w, by + bar_h, r=3, fill=fill_col, outline="", tags="row_item")

            # Active shimmer wave sweep (if downloading and motion not reduced)
            if "downloading" in tags and not is_reduced_motion() and fill_w > 8:
                shim_w = 16
                shim_x = bx + int((self._shimmer_phase * (fill_w + shim_w))) - shim_w
                clamped_x1 = max(bx, shim_x)
                clamped_x2 = min(bx + fill_w, shim_x + shim_w)
                if clamped_x2 > clamped_x1:
                    self.viewport.create_rectangle(clamped_x1, by + 1, clamped_x2, by + bar_h - 1, fill="#ffffff", outline="", tags="row_item")

        self.viewport.create_text(bx + bar_w + 8, mid_y, text=pct_text, font=("Consolas", 8), fill=THEME["text_secondary"], anchor=tk.W, tags="row_item")

        # 7. Col 4: Speed (Right-aligned cool slate under SPEED header)
        speed_right_x = col_x["speed"] + self._col_config["speed"]["width"] - 14
        self.viewport.create_text(speed_right_x, mid_y, text=speed_str, font=("Consolas", 9), fill=THEME["text_secondary"], anchor=tk.E, tags="row_item")

        # 8. Col 5: URL (Dimmed slate-450 with ellipsis under DOWNLOAD URL header)
        url_left_x = col_x["url"] + 14
        avail_url_w = max(80, vw - url_left_x - 14)
        disp_url = self._fit_text_with_ellipsis(url_str, avail_url_w, (FONT_DISPLAY, 8))
        self.viewport.create_text(url_left_x, mid_y, text=disp_url, font=(FONT_DISPLAY, 8), fill=THEME["text_subtle"], anchor=tk.W, tags="row_item")

    def _render_empty_state(self, vw: int, vh: int):
        cx = vw // 2
        cy = vh // 2

        card_w = min(420, max(280, vw - 60))
        card_h = 176
        x1 = cx - (card_w // 2)
        y1 = cy - (card_h // 2)
        x2 = x1 + card_w
        y2 = y1 + card_h

        # Render smooth supersampled Liquid Glass empty state pod
        drew_glass_card = False
        if vw >= 60 and vh >= 60:
            try:
                top_w = self.viewport.winfo_toplevel()
                rx = max(0, self.viewport.winfo_rootx() - top_w.winfo_rootx() + x1)
                ry = max(0, self.viewport.winfo_rooty() - top_w.winfo_rooty() + y1)
                key = (card_w, card_h, rx, ry)
                if key != self._empty_card_key or self._empty_card_photo is None:
                    self._empty_card_photo = AmbientMeshEngine.get_shared().create_glass_panel(
                        w=card_w,
                        h=card_h,
                        r=RADIUS_LG,
                        root_x=rx,
                        root_y=ry,
                        tint_rgba=(12, 20, 34, 155),
                        border_rgba=(70, 110, 170, 190),
                        specular=True,
                        caustic=True,
                    )
                    self._empty_card_key = key
                self.viewport.create_image(x1, y1, image=self._empty_card_photo, anchor=tk.NW, tags="empty_state")
                drew_glass_card = True
            except Exception:
                drew_glass_card = False

        if not drew_glass_card:
            draw_liquid_glass_panel(
                self.viewport,
                x1, y1, x2, y2,
                r=RADIUS_LG,
                fill=THEME["tree_bg"],
                border=THEME["glass_border"],
                rim_highlight=THEME["glass_rim"],
                refraction=THEME["glass_refraction"],
                shadow=True,
                tags="empty_state",
            )

        # Vector Download Tray Glyph
        self.viewport.create_text(cx, cy - 44, text="📥", font=(FONT_DISPLAY, 24), fill=THEME["accent_glow"], anchor=tk.CENTER, tags="empty_state")
        self.viewport.create_text(cx, cy - 10, text=tr("empty_title"), font=(FONT_DISPLAY, 11, "bold"), fill=THEME["text_primary"], anchor=tk.CENTER, tags="empty_state")
        self.viewport.create_text(cx, cy + 15, text=tr("empty_desc"), font=(FONT_DISPLAY, 8), fill=THEME["text_tertiary"], anchor=tk.CENTER, width=card_w - 48, justify=tk.CENTER, tags="empty_state")

        # Quick Action Button
        btn_w = 180
        btn_h = 30
        bx1 = cx - (btn_w // 2)
        by1 = cy + 42
        bx2 = bx1 + btn_w
        by2 = by1 + btn_h
        self._empty_btn_bounds = (bx1, by1, bx2, by2)
        draw_round_rectangle(self.viewport, bx1, by1, bx2, by2, r=15, fill=THEME["accent_primary"], outline=THEME["accent_glow"], tags=("empty_state", "empty_btn"))
        self.viewport.create_text(cx, by1 + (btn_h // 2), text=tr("empty_btn"), font=(FONT_DISPLAY, 8, "bold"), fill="#ffffff", anchor=tk.CENTER, tags=("empty_state", "empty_btn"))

    # =========================================================================
    # SHIMMER WAVE ANIMATION LOOP
    # =========================================================================

    def _schedule_shimmer(self):
        if is_reduced_motion() or os.environ.get("PYTEST_CURRENT_TEST"):
            return

        def _step():
            self._shimmer_timer_id = None
            if not self.winfo_exists():
                return

            # Only animate if window is mapped and there are downloading rows
            has_downloading = any("downloading" in self._data.get(iid, {}).get("tags", ()) for iid in self._items)
            if has_downloading:
                self._shimmer_phase = (self._shimmer_phase + 0.04) % 1.0
                self._render_viewport()
                # Active shimmer: 50ms = 20 FPS
                self._shimmer_timer_id = self.after(50, _step)
            else:
                # Idle: check once per second
                self._shimmer_timer_id = self.after(1000, _step)

        self._shimmer_timer_id = self.after(100, _step)

    # =========================================================================
    # HELPERS: ICONS, STATUS STYLES, TEXT TRUNCATION
    # =========================================================================

    def _get_file_icon(self, filename: str) -> str:
        fn = filename.lower()
        if fn.endswith((".mp4", ".mkv", ".avi", ".mov", ".webm", ".ts", ".m4v", ".flv")):
            return "🎬"
        elif fn.endswith((".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma")):
            return "🎵"
        elif fn.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico")):
            return "🖼"
        elif fn.endswith((".exe", ".msi", ".bat", ".cmd", ".ps1", ".iso", ".apk", ".dmg", ".app")):
            return "📦"
        elif fn.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv")):
            return "📄"
        elif fn.endswith((".zip", ".rar", ".7z", ".tar", ".gz", ".bz2")):
            return "🗜"
        return "📄"

    def _get_status_style(self, status: str, tags: tuple) -> tuple[str, str]:
        st = status.lower()
        if "completed" in tags or "selesai" in st or "completed" in st:
            return "●", THEME["success"]
        elif "downloading" in tags or "mengunduh" in st or "downloading" in st:
            return "●", THEME["accent_glow"]
        elif "paused" in tags or "dijeda" in st or "paused" in st:
            return "●", THEME["warning"]
        elif "failed" in tags or "error" in tags or "gagal" in st or "failed" in st:
            return "●", THEME["danger"]
        return "●", THEME["text_secondary"]

    def _parse_progress(self, prog_str: str) -> tuple[float, str]:
        if not prog_str:
            return 0.0, "0.0%"
        import re
        m = re.search(r"(\d+(?:\.\d+)?)%", prog_str)
        if m:
            val = float(m.group(1))
            return min(1.0, max(0.0, val / 100.0)), f"{val:.1f}%"
        return 0.0, prog_str

    def _fit_text_with_ellipsis(self, text: str, max_w: int, font_spec: tuple) -> str:
        if not text or max_w <= 20:
            return text
        try:
            f = tkfont.Font(font=font_spec)
            if f.measure(text) <= max_w:
                return text
            # Binary search for max chars that fit (O(log n) instead of O(n))
            ellipsis = "..."
            ell_w = f.measure(ellipsis)
            sub_w = max_w - ell_w
            lo, hi = 0, len(text)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if f.measure(text[:mid]) <= sub_w:
                    lo = mid
                else:
                    hi = mid - 1
            return text[:lo] + ellipsis if lo > 0 else text[:4] + ellipsis
        except Exception:
            return text[:30] + "..." if len(text) > 30 else text

    # =========================================================================
    # TTK.TREEVIEW DROP-IN COMPATIBILITY API
    # =========================================================================

    def insert(self, parent: str, index: Any, iid: Optional[str] = None, **kwargs) -> str:
        row_id = str(iid) if iid is not None else f"row_{len(self._items)}_{time.time()}"
        values = list(kwargs.get("values", ()))
        tags = tuple(kwargs.get("tags", ()))

        if row_id in self._data:
            # Overwrite existing
            self._data[row_id]["values"] = values
            self._data[row_id]["tags"] = tags
        else:
            self._data[row_id] = {"values": values, "tags": tags}
            if index == "end" or index >= len(self._items):
                self._items.append(row_id)
            else:
                self._items.insert(int(index), row_id)

        self._update_scroll_bounds()
        self._schedule_coalesced_render()
        return row_id

    def delete(self, *items):
        for item in items:
            iid = str(item)
            if iid in self._items:
                self._items.remove(iid)
            if iid in self._data:
                del self._data[iid]
            if iid in self._selected_ids:
                self._selected_ids.remove(iid)
        self._update_scroll_bounds()
        self._render_viewport()

    def exists(self, iid: str) -> bool:
        return str(iid) in self._data

    def get_children(self, parent: str = "") -> tuple[str, ...]:
        return tuple(self._items)

    def item(self, iid: str, option: Optional[str] = None, **kwargs) -> Any:
        row_id = str(iid)
        if row_id not in self._data:
            return {}
        if "values" in kwargs:
            self._data[row_id]["values"] = list(kwargs["values"])
        if "tags" in kwargs:
            self._data[row_id]["tags"] = tuple(kwargs["tags"])
        if kwargs:
            self._schedule_coalesced_render()

        rec = self._data[row_id]
        if option == "values":
            return rec.get("values", [])
        elif option == "tags":
            return rec.get("tags", ())
        return rec

    def selection(self) -> tuple[str, ...]:
        # Return selected IDs in display order
        return tuple(iid for iid in self._items if iid in self._selected_ids)

    def selection_set(self, *items):
        if len(items) == 1 and isinstance(items[0], (list, tuple, set)):
            flat_items = items[0]
        else:
            flat_items = items
        self._selected_ids = {str(item) for item in flat_items if str(item) in self._data}
        if self._selected_ids:
            self._anchor_id = list(self._selected_ids)[-1]
        self._schedule_coalesced_render()

    def selection_add(self, *items):
        if len(items) == 1 and isinstance(items[0], (list, tuple, set)):
            flat_items = items[0]
        else:
            flat_items = items
        for item in flat_items:
            iid = str(item)
            if iid in self._data:
                self._selected_ids.add(iid)
        self._schedule_coalesced_render()

    def selection_remove(self, *items):
        if len(items) == 1 and isinstance(items[0], (list, tuple, set)):
            flat_items = items[0]
        else:
            flat_items = items
        for item in flat_items:
            self._selected_ids.discard(str(item))
        self._schedule_coalesced_render()

    def selection_clear(self, **kwargs):
        self._selected_ids.clear()
        self._anchor_id = None
        self._schedule_coalesced_render()

    def identify_row(self, y: int) -> Optional[str]:
        return self._get_row_at_y(y)

    def heading(self, column: str, option: Optional[str] = None, **kwargs) -> Any:
        if column not in self._col_config:
            return ""
        if option == "text":
            return self._col_config[column].get("title", "")
        if "text" in kwargs:
            self._col_config[column]["title"] = kwargs["text"]
        if "command" in kwargs:
            self._col_config[column]["command"] = kwargs["command"]
        if option is None and not kwargs:
            return self._col_config[column]
        self._redraw_header()
        return self._col_config[column].get("title", "")

    def column(self, column: str, option: Optional[str] = None, **kwargs) -> Any:
        if column not in self._col_config:
            return ""
        if option == "width":
            return self._col_config[column].get("width", 100)
        if "width" in kwargs:
            self._col_config[column]["width"] = kwargs["width"]
        if "minwidth" in kwargs:
            self._col_config[column]["minwidth"] = kwargs["minwidth"]
        if "anchor" in kwargs:
            self._col_config[column]["anchor"] = kwargs["anchor"]
        if option is None and not kwargs:
            return self._col_config[column]
        self._redraw_header()
        self._render_viewport()
        return self._col_config[column].get("width", 100)

    def tag_configure(self, tag: str, **kwargs):
        # Kept for compatibility with Treeview.tag_configure
        pass

    def move(self, item: str, parent: str, index: int):
        iid = str(item)
        if iid in self._items:
            self._items.remove(iid)
            self._items.insert(min(len(self._items), max(0, int(index))), iid)
            self._render_viewport()

    def yview(self, *args):
        # Kept for compatibility with Treeview.yview
        pass

    def bind(self, sequence=None, func=None, add=None, *args, **kwargs):
        if sequence and str(sequence).startswith(("<Double-1>", "<Button-3>", "<<TreeviewSelect>>", "<Delete>")):
            if sequence not in self._custom_bindings:
                self._custom_bindings[str(sequence)] = []
            if func:
                self._custom_bindings[str(sequence)].append(func)
        return super().bind(sequence, func, add=add)

    def _trigger_custom_binding(self, sequence: str, event):
        callbacks = self._custom_bindings.get(sequence, [])
        for cb in callbacks:
            try:
                cb(event)
            except Exception as e:
                print(f"Error in {sequence} callback:", e)
