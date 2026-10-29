"""Model data dan dataclass untuk AutoSign Pro."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SignatureConfig:
    """Konfigurasi koordinat relatif untuk satu tanda tangan atau stempel."""
    label: str
    rel_x: float
    rel_y: float
    rel_w: float
    rel_h: float
    page: int = 0  # 0 = halaman pertama, -1 = halaman terakhir, n = indeks halaman ke-n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "rel_x": self.rel_x,
            "rel_y": self.rel_y,
            "rel_w": self.rel_w,
            "rel_h": self.rel_h,
            "page": self.page,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignatureConfig":
        return cls(
            label=data["label"],
            rel_x=float(data["rel_x"]),
            rel_y=float(data["rel_y"]),
            rel_w=float(data["rel_w"]),
            rel_h=float(data["rel_h"]),
            page=int(data.get("page", 0)),
        )


@dataclass
class Profile:
    """Model data untuk satu profil layout tanda tangan."""
    name: str
    keywords: List[str]
    signatures: List[SignatureConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "keywords": self.keywords,
            "signatures": [s.to_dict() for s in self.signatures]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        # Backward compatibility jika keywords berupa string tunggal atau list
        raw_keywords = data.get("keywords")
        if raw_keywords is None:
            raw_keywords = [data.get("keyword", "KARTIR")]
        elif isinstance(raw_keywords, str):
            raw_keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]

        signatures = [
            SignatureConfig.from_dict(s)
            for s in data.get("signatures", [])
        ]
        return cls(
            name=data.get("name", "New_Profile"),
            keywords=raw_keywords,
            signatures=signatures
        )


@dataclass
class ProcessingTask:
    """Tugas pemrosesan untuk satu dokumen PDF."""
    pdf_path: str
    save_path: str
    profile: Profile
    ttd_root: str
    rel_path: str


@dataclass
class ProcessResult:
    """Hasil eksekusi pembubuhan tanda tangan pada satu PDF."""
    success: bool
    error_message: Optional[str] = None
    task: Optional[ProcessingTask] = None


@dataclass
class AppSettings:
    """Konfigurasi path master pengguna."""
    pdf_root: str = ""
    ttd_master: str = ""
    output_dir: str = ""

    @property
    def signature_root(self) -> str:
        """Alias nama deskriptif untuk ttd_master."""
        return self.ttd_master

    @signature_root.setter
    def signature_root(self, value: str) -> None:
        self.ttd_master = value

    def to_dict(self) -> Dict[str, str]:
        return {
            "pdf": self.pdf_root,
            "ttd": self.ttd_master,
            "out": self.output_dir
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "AppSettings":
        return cls(
            pdf_root=data.get("pdf", ""),
            ttd_master=data.get("ttd") or data.get("signature_root", ""),
            output_dir=data.get("out", "")
        )
