import json
import os
import sys
from typing import Optional

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_RUN_NAME = "JustPressDownload"


def set_windows_startup(enabled: bool) -> bool:
    """Registers or unregisters JustPressDownload in Windows HKCU Run key."""
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                exe_candidates = [
                    os.path.abspath("JustPressDownload.exe"),
                    os.path.abspath("dist/JustPressDownload.exe"),
                ]
                target_exe = None
                for c in exe_candidates:
                    if os.path.exists(c):
                        target_exe = c
                        break
                if not target_exe:
                    if getattr(sys, "frozen", False):
                        target_exe = sys.executable
                    else:
                        target_exe = os.path.abspath("run_gui.bat")
                winreg.SetValueEx(key, APP_RUN_NAME, 0, winreg.REG_SZ, f'"{target_exe}"')
            else:
                try:
                    winreg.DeleteValue(key, APP_RUN_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def get_windows_startup_status() -> bool:
    """Checks if JustPressDownload is registered in Windows startup registry."""
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ
        ) as key:
            try:
                winreg.QueryValueEx(key, APP_RUN_NAME)
                return True
            except FileNotFoundError:
                return False
    except Exception:
        return False


class SettingsManager:
    """Manages persistent application settings, such as remembered category download paths."""

    DEFAULT_CATEGORIES = {
        "Video": "Video",
        "Musik": "Music",
        "Gambar": "Pictures",
        "Program": "Programs",
        "Dokumen": "Documents",
        "Berkas Terkompresi": "Compressed",
        "Umum": "General",
    }

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = os.path.abspath(config_path)
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".idm_clone")
            os.makedirs(base_dir, exist_ok=True)
            self.config_path = os.path.join(base_dir, "settings.json")

        self.data: dict = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def get_category_path(self, category: str, default_base: Optional[str] = None) -> str:
        cat_paths = self.data.get("category_paths", {})
        if category in cat_paths:
            return cat_paths[category]

        base = default_base or os.path.join(os.path.expanduser("~"), "Downloads")
        sub = self.DEFAULT_CATEGORIES.get(category, category)
        default_folder = os.path.join(base, sub)
        return default_folder

    def set_category_path(self, category: str, folder: str) -> None:
        if "category_paths" not in self.data:
            self.data["category_paths"] = {}
        abs_folder = os.path.abspath(folder)
        try:
            os.makedirs(abs_folder, exist_ok=True)
        except Exception:
            pass
        self.data["category_paths"][category] = abs_folder
        self._save()

    def get_max_connections(self) -> int:
        return int(self.data.get("max_connections", 8))

    def set_max_connections(self, count: int) -> None:
        self.data["max_connections"] = int(count)
        self._save()

    def get_close_to_tray(self) -> bool:
        return bool(self.data.get("close_to_tray", True))

    def set_close_to_tray(self, val: bool) -> None:
        self.data["close_to_tray"] = bool(val)
        self._save()

    def get_autorun_startup(self) -> bool:
        return bool(self.data.get("autorun_startup", True))

    def set_autorun_startup(self, val: bool) -> None:
        self.data["autorun_startup"] = bool(val)
        self._save()
        set_windows_startup(bool(val))

    def get_start_minimized(self) -> bool:
        return bool(self.data.get("start_minimized", False))

    def set_start_minimized(self, val: bool) -> None:
        self.data["start_minimized"] = bool(val)
        self._save()

    def get_play_sound_on_complete(self) -> bool:
        return bool(self.data.get("play_sound_on_complete", True))

    def set_play_sound_on_complete(self, val: bool) -> None:
        self.data["play_sound_on_complete"] = bool(val)
        self._save()

    def get_confirm_on_delete(self) -> bool:
        return bool(self.data.get("confirm_on_delete", True))

    def set_confirm_on_delete(self, val: bool) -> None:
        self.data["confirm_on_delete"] = bool(val)
        self._save()

    def get_autoclose_progress(self) -> bool:
        return bool(self.data.get("autoclose_progress", False))

    def set_autoclose_progress(self, val: bool) -> None:
        self.data["autoclose_progress"] = bool(val)
        self._save()


# Global default instance
settings = SettingsManager()
