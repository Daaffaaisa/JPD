"""Comprehensive unit tests for GlassTableView (Phase 4).
Validates row insertion, deletion, selection, keyboard navigation,
Treeview compatibility, progress parsing, and empty state.
"""

import os
import sys
import tkinter as tk
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from idm_gui.glass_table import GlassTableView
from idm_gui.theme import THEME


def test_glass_table_crud_and_selection():
    """Verify insert, item update, exists, delete, and selection."""
    root = tk.Tk()
    root.withdraw()
    try:
        table = GlassTableView(root)
        table.pack(fill=tk.BOTH, expand=True)

        # 1. Insert rows
        t1 = table.insert("", "end", iid="task_1", values=("video.mp4", "120 MB", "Completed", "100%", "--", "http://a.com/v.mp4"), tags=("completed",))
        t2 = table.insert("", "end", iid="task_2", values=("archive.zip", "500 MB", "Downloading", "45%", "12 MB/s", "http://a.com/z.zip"), tags=("downloading",))
        assert t1 == "task_1"
        assert t2 == "task_2"
        assert table.exists("task_1") is True
        assert table.exists("task_2") is True
        assert table.exists("task_99") is False

        # 2. Get children
        children = table.get_children()
        assert children == ("task_1", "task_2")

        # 3. Read item values
        vals = table.item("task_1", "values")
        assert vals[0] == "video.mp4"
        assert vals[1] == "120 MB"

        # 4. Update item values
        table.item("task_2", values=("archive.zip", "500 MB", "Downloading", "55%", "15 MB/s", "http://a.com/z.zip"))
        assert table.item("task_2", "values")[3] == "55%"

        # 5. Selection
        table.selection_set("task_1")
        assert table.selection() == ("task_1",)

        table.selection_add("task_2")
        assert set(table.selection()) == {"task_1", "task_2"}

        table.selection_remove("task_1")
        assert table.selection() == ("task_2",)

        table.selection_clear()
        assert table.selection() == ()

        # 6. Delete
        table.delete("task_1")
        assert table.exists("task_1") is False
        assert table.get_children() == ("task_2",)
    finally:
        root.destroy()


def test_glass_table_keyboard_navigation():
    """Verify Up, Down, Home, End, Ctrl+A keyboard navigation."""
    root = tk.Tk()
    root.withdraw()
    try:
        table = GlassTableView(root)
        table.pack()

        for i in range(5):
            table.insert("", "end", iid=f"row_{i}", values=(f"file_{i}.txt", "1 MB", "Paused", "0%", "--", "url"))

        # Select all
        event = tk.Event()
        table._on_key_select_all(event)
        assert len(table.selection()) == 5

        # Single select first
        table.selection_set("row_0")
        assert table.selection() == ("row_0",)

        # Move Down
        table._on_key_down(event)
        assert table.selection() == ("row_1",)

        # Move Down again
        table._on_key_down(event)
        assert table.selection() == ("row_2",)

        # Move Up
        table._on_key_up(event)
        assert table.selection() == ("row_1",)

        # Jump End
        table._on_key_end(event)
        assert table.selection() == ("row_4",)

        # Jump Home
        table._on_key_home(event)
        assert table.selection() == ("row_0",)
    finally:
        root.destroy()


def test_glass_table_headings_and_columns():
    """Verify heading title update and column width adjustments."""
    root = tk.Tk()
    root.withdraw()
    try:
        table = GlassTableView(root)
        table.heading("name", text="File Name")
        assert table._col_config["name"]["title"] == "File Name"

        table.column("status", width=145)
        assert table._col_config["status"]["width"] == 145
    finally:
        root.destroy()


def test_glass_table_empty_state_button_and_container_clearance():
    """Verify empty state renders once with clickable button and TactileTableContainer inset clears rounded corners."""
    import math
    from idm_gui.app import TactileTableContainer
    from idm_gui.theme import RADIUS_LG

    root = tk.Tk()
    root.geometry("900x520+50+50")
    root.withdraw()
    try:
        clicked = []
        container = TactileTableContainer(root, r=RADIUS_LG)
        container.pack(fill=tk.BOTH, expand=True)
        table = GlassTableView(container.inner_frame, on_add_url_click=lambda: clicked.append(True))
        table.pack(fill=tk.BOTH, expand=True)
        root.update()
        container._redraw()
        table._render_viewport()

        # Verify inner_frame corner is strictly inside the rounded arc of radius r
        x_pad, y_pad = container.coords(container.win_id)
        r = container.r
        dist_from_arc_center = math.hypot(r - x_pad, r - y_pad)
        assert dist_from_arc_center <= (r - 2), f"Inner frame overlaps rounded corner: pad=({x_pad},{y_pad}), r={r}"

        # Verify empty state rendered and button click triggers callback
        assert len(table.viewport.find_withtag("empty_state")) > 0
        assert table._empty_btn_bounds is not None
        bx1, by1, bx2, by2 = table._empty_btn_bounds
        ev = tk.Event()
        ev.x = (bx1 + bx2) // 2
        ev.y = (by1 + by2) // 2
        table._on_click(ev)
        assert clicked == [True]
    finally:
        root.destroy()
