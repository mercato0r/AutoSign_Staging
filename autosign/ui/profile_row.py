"""Komponen widget baris kartu profil pada daftar profil."""

from typing import Callable
import customtkinter as ctk
from autosign.constants import COLOR_DANGER, COLOR_DANGER_HOVER, COLOR_ACCENT
from autosign.models import Profile


class ProfileRowItem(ctk.CTkFrame):
    """Widget baris untuk satu profil pada daftar manajemen profil."""

    def __init__(
        self,
        parent,
        filename: str,
        profile: Profile,
        is_selected_var: ctk.BooleanVar,
        on_delete: Callable[[str, str], None],
        on_copy: Callable[[Profile], None],
        on_edit: Callable[[Profile], None],
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.filename = filename
        self.profile = profile

        keywords_text = ", ".join(profile.keywords)
        display_label = f"{profile.name} ({keywords_text})"

        # Checkbox Pemilihan Profil
        self.checkbox = ctk.CTkCheckBox(
            self, text=display_label, variable=is_selected_var
        )
        self.checkbox.pack(side="left", padx=5)

        # Tombol Aksi: Hapus, Salin, Edit
        self.btn_delete = ctk.CTkButton(
            self, text="X", width=30, height=20,
            fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
            command=lambda: on_delete(filename, profile.name)
        )
        self.btn_delete.pack(side="right", padx=2)

        self.btn_copy = ctk.CTkButton(
            self, text="Copy", width=40, height=20,
            fg_color=COLOR_ACCENT,
            command=lambda: on_copy(profile)
        )
        self.btn_copy.pack(side="right", padx=2)

        self.btn_edit = ctk.CTkButton(
            self, text="Edit", width=40, height=20,
            command=lambda: on_edit(profile)
        )
        self.btn_edit.pack(side="right", padx=2)
