"""Layanan manajemen CRUD profil tata letak tanda tangan."""

import os
import json
import re
from typing import List, Tuple, Optional
from autosign.constants import PROFILES_DIR_NAME
from autosign.models import Profile


class ProfileService:
    def __init__(self, profiles_dir: str = PROFILES_DIR_NAME):
        self.profiles_dir = profiles_dir
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Memastikan direktori profil selalu ada."""
        os.makedirs(self.profiles_dir, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Membersihkan nama file dari karakter ilegal Windows."""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()

    def get_profile_path(self, filename_or_name: str) -> str:
        """Menghasilkan path absolut/relatif aman untuk file profil."""
        if not filename_or_name.endswith(".json"):
            filename_or_name = f"{filename_or_name}.json"
        return os.path.join(self.profiles_dir, filename_or_name)

    def list_profiles(self) -> List[Tuple[str, Profile]]:
        """Membaca seluruh profil dari folder profiles/."""
        self._ensure_dir()
        profiles: List[Tuple[str, Profile]] = []
        if not os.path.exists(self.profiles_dir):
            return profiles

        for filename in sorted(os.listdir(self.profiles_dir)):
            if filename.lower().endswith(".json"):
                filepath = os.path.join(self.profiles_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        profile = Profile.from_dict(data)
                        profiles.append((filename, profile))
                except Exception:
                    # Lewati profil yang korup/tidak valid agar tidak memutus listing profil lain
                    continue
        return profiles

    def save_profile(self, profile: Profile) -> str:
        """Menyimpan profil ke disk. Mengembalikan nama file yang disimpan."""
        self._ensure_dir()
        safe_name = self._sanitize_filename(profile.name)
        if not safe_name:
            safe_name = "New_Profile"
        profile.name = safe_name

        filepath = self.get_profile_path(safe_name)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=4)
        return os.path.basename(filepath)

    def delete_profile(self, filename: str) -> bool:
        """Menghapus file profil dari disk."""
        filepath = os.path.join(self.profiles_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except OSError:
                return False
        return False

    def duplicate_profile(self, source_profile: Profile) -> Profile:
        """Membuat salinan profil baru dengan penomoran unik yang tidak menimpa profil lama."""
        self._ensure_dir()
        base_name = f"{source_profile.name}_Copy"
        candidate_name = base_name
        counter = 1

        while os.path.exists(self.get_profile_path(candidate_name)):
            candidate_name = f"{base_name}_{counter}"
            counter += 1

        new_profile = Profile(
            name=candidate_name,
            keywords=list(source_profile.keywords),
            signatures=list(source_profile.signatures)
        )
        self.save_profile(new_profile)
        return new_profile
