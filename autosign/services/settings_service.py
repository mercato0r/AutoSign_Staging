"""Layanan persistensi pengaturan pengguna (settings.json)."""

import os
import json
from autosign.constants import SETTINGS_FILE_NAME
from autosign.models import AppSettings


class SettingsService:
    def __init__(self, filepath: str = SETTINGS_FILE_NAME):
        self.filepath = filepath

    def load_settings(self) -> AppSettings:
        """Memuat pengaturan dari disk. Mengembalikan default jika file tidak ditemukan atau korup."""
        if not os.path.exists(self.filepath):
            return AppSettings()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppSettings.from_dict(data)
        except Exception:
            return AppSettings()

    def save_settings(self, settings: AppSettings) -> bool:
        """Menyimpan pengaturan ke disk."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(settings.to_dict(), f, indent=4)
            return True
        except Exception:
            return False
