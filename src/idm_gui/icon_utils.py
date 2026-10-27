import ctypes
from ctypes import wintypes
import os
from typing import Optional
from PIL import Image, ImageDraw


class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


# Cache extracted icons by (extension, size) to prevent repeated Windows API calls
_ICON_CACHE: dict[tuple[str, int], Image.Image] = {}


def _create_fallback_icon(size: int = 32) -> Image.Image:
    """Creates a clean fallback icon for files without registered Windows association."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # File document shape
    draw.rectangle([4, 2, size - 4, size - 2], fill=(45, 120, 220, 255), outline=(25, 80, 180, 255))
    # Folded corner
    draw.polygon([(size - 10, 2), (size - 4, 8), (size - 10, 8)], fill=(180, 215, 255, 255))
    return img


def get_extension_icon_image(filename_or_ext: str, size: int = 32) -> Image.Image:
    """
    Extracts the native Windows registered default application icon for the given file extension.
    (e.g., VLC cone for .mp4, WinRAR/7-Zip for .zip, Acrobat for .pdf).
    """
    if not filename_or_ext:
        return _create_fallback_icon(size)

    # Extract extension
    ext = os.path.splitext(filename_or_ext)[1].lower()
    if not ext and filename_or_ext.startswith("."):
        ext = filename_or_ext.lower()
    if not ext:
        ext = ".bin"

    cache_key = (ext, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key].copy()

    if os.name != "nt":
        img = _create_fallback_icon(size)
        _ICON_CACHE[cache_key] = img
        return img.copy()

    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        shell32 = ctypes.windll.shell32

        gdi32.GetDIBits.argtypes = [
            wintypes.HDC,
            wintypes.HBITMAP,
            wintypes.UINT,
            wintypes.UINT,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.UINT,
        ]
        gdi32.GetDIBits.restype = ctypes.c_int

        user32.GetDC.argtypes = [wintypes.HWND]
        user32.GetDC.restype = wintypes.HDC

        user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        user32.ReleaseDC.restype = ctypes.c_int

        user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(ICONINFO)]
        user32.GetIconInfo.restype = wintypes.BOOL

        user32.DestroyIcon.argtypes = [wintypes.HICON]
        user32.DestroyIcon.restype = wintypes.BOOL

        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        gdi32.DeleteObject.restype = wintypes.BOOL

        SHGFI_ICON = 0x000000100
        SHGFI_LARGEICON = 0x000000000  # 32x32
        SHGFI_USEFILEATTRIBUTES = 0x000000010
        FILE_ATTRIBUTE_NORMAL = 0x00000080

        sfi = SHFILEINFOW()
        res = shell32.SHGetFileInfoW(
            ext,
            FILE_ATTRIBUTE_NORMAL,
            ctypes.byref(sfi),
            ctypes.sizeof(sfi),
            SHGFI_ICON | SHGFI_USEFILEATTRIBUTES | SHGFI_LARGEICON,
        )

        if not res or not sfi.hIcon:
            img = _create_fallback_icon(size)
            _ICON_CACHE[cache_key] = img
            return img.copy()

        hIcon = sfi.hIcon
        icon_info = ICONINFO()
        if not user32.GetIconInfo(hIcon, ctypes.byref(icon_info)):
            user32.DestroyIcon(hIcon)
            img = _create_fallback_icon(size)
            _ICON_CACHE[cache_key] = img
            return img.copy()

        hdc = user32.GetDC(None)
        bih = BITMAPINFOHEADER()
        bih.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bih.biWidth = 32
        bih.biHeight = -32  # Top-down bitmap
        bih.biPlanes = 1
        bih.biBitCount = 32
        bih.biCompression = 0  # BI_RGB

        buf = ctypes.create_string_buffer(32 * 32 * 4)
        gdi32.GetDIBits(hdc, icon_info.hbmColor, 0, 32, buf, ctypes.byref(bih), 0)
        user32.ReleaseDC(None, hdc)

        raw_data = bytearray(buf.raw)
        has_alpha = any(raw_data[i + 3] > 0 for i in range(0, len(raw_data), 4))
        if not has_alpha:
            for i in range(0, len(raw_data), 4):
                raw_data[i + 3] = 255

        img = Image.frombuffer("RGBA", (32, 32), bytes(raw_data), "raw", "BGRA", 0, 1)

        # Cleanup Win32 handles
        gdi32.DeleteObject(icon_info.hbmColor)
        gdi32.DeleteObject(icon_info.hbmMask)
        user32.DestroyIcon(hIcon)

        if size != 32:
            img = img.resize((size, size), Image.Resampling.LANCZOS)

        _ICON_CACHE[cache_key] = img
        return img.copy()
    except Exception:
        img = _create_fallback_icon(size)
        _ICON_CACHE[cache_key] = img
        return img.copy()
