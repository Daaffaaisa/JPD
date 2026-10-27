import json
import os
from typing import Optional


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


# Global default instance
settings = SettingsManager()
