import os
import pytest
import tkinter as tk
from idm_gui.theme import (
    THEME,
    RADIUS_XS,
    RADIUS_SM,
    RADIUS_MD,
    RADIUS_LG,
    RADIUS_XL,
    RADIUS_2XL,
    draw_round_rectangle,
    draw_liquid_glass_panel,
    draw_skeleton_shimmer,
    is_reduced_motion,
    interpolate_color,
    hex_to_rgb,
    rgb_to_hex,
    create_modern_button,
    RoundedButton,
)


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_liquid_glass_color_math():
    """Verify hex and RGB interpolation mathematics for smooth glass glow."""
    rgb = hex_to_rgb("#007aff")
    assert rgb == (0, 122, 255)
    assert rgb_to_hex(rgb) == "#007aff"

    # Middle interpolation
    mid = interpolate_color("#000000", "#ffffff", 0.5)
    assert mid == "#7f7f7f"


def test_draw_liquid_glass_panel(tk_root):
    """Verify liquid glass panel renders layered drop shadow, frosted body, and specular rims."""
    canvas = tk.Canvas(tk_root, width=300, height=200, bg=THEME["bg_dark"])
    canvas.pack()
    tk_root.update()

    item_ids = draw_liquid_glass_panel(
        canvas,
        x1=10,
        y1=10,
        x2=280,
        y2=180,
        r=RADIUS_LG,
        fill=THEME["surface"],
        border=THEME["glass_border"],
        rim_highlight=THEME["glass_rim"],
        refraction=THEME["glass_refraction"],
        shadow=True,
    )
    # Must create shadow, body, and specular lines
    assert len(item_ids) >= 4
    for item_id in item_ids:
        assert canvas.type(item_id) in ("polygon", "line")


def test_draw_skeleton_shimmer(tk_root):
    """Verify skeleton shimmer bar creates valid canvas primitives."""
    canvas = tk.Canvas(tk_root, width=200, height=50, bg=THEME["bg_dark"])
    canvas.pack()
    tk_root.update()

    draw_skeleton_shimmer(canvas, x1=10, y1=10, x2=190, y2=40, r=RADIUS_SM, phase=0.4)
    items = canvas.find_all()
    assert len(items) >= 2


def test_liquid_glass_button_hover_and_reduced_motion(tk_root, monkeypatch):
    """Verify RoundedButton Liquid Glass transitions and reduced motion obedience."""
    btn = create_modern_button(tk_root, text="Test Glass", kind="primary")
    btn.pack()
    tk_root.update()

    assert isinstance(btn, RoundedButton)
    assert btn.radius == RADIUS_MD

    # Normal hover animation
    btn._on_enter(None)
    tk_root.update()
    btn._on_leave(None)
    tk_root.update()

    # Reduced motion flag
    monkeypatch.setenv("REDUCED_MOTION", "1")
    assert is_reduced_motion() is True
    btn._on_enter(None)
    assert btn._glow_alpha == 1.0
    btn._on_leave(None)
    assert btn._glow_alpha == 0.0
