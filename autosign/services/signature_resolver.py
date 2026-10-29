"""Resolusi hirarki path file gambar tanda tangan/stempel."""

import os
from typing import Optional


class SignatureResolver:
    """Mencari file gambar tanda tangan (.png) berdasarkan hirarki prioritas folder."""

    @staticmethod
    def resolve(ttd_root: str, rel_path: str, label: str) -> Optional[str]:
        """
        Mencari path absolut file gambar tanda tangan dengan 3 tingkat pencarian:
        1. Subdirektori relatif yang sama persis dengan posisi file PDF terhadap pdf_root.
        2. Segmen folder parent (pencarian mundur dari parent terdekat hingga ke atas).
        3. Root direktori master tanda tangan (fallback).
        """
        filename = f"{label}.png"
        normalized_rel = os.path.normpath(rel_path)
        path_segments = normalized_rel.split(os.sep)

        # Tingkat 1: Subfolder persis
        exact_subfolder_path = os.path.join(ttd_root, os.path.dirname(normalized_rel), filename)
        if os.path.exists(exact_subfolder_path):
            return exact_subfolder_path

        # Tingkat 2: Segmen parent terdekat (reversed walk)
        for seg in reversed(path_segments[:-1]):
            candidate_path = os.path.join(ttd_root, seg, filename)
            if os.path.exists(candidate_path):
                return candidate_path

        # Tingkat 3: Fallback ke root master folder
        root_path = os.path.join(ttd_root, filename)
        if os.path.exists(root_path):
            return root_path

        return None
