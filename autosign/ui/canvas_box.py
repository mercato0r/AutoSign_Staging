"""Representasi kotak visual tanda tangan pada canvas preview."""

import tkinter as tk
from typing import Optional, List
from autosign.constants import ARC_BLUE, COLOR_WARNING
from autosign.models import SignatureConfig

HANDLE_SIZE = 12  # Ukuran handle resize yang mudah diklik pada berbagai resolusi


class CanvasSignatureBox:
    """Mengelola render visual kotak tanda tangan pada canvas Tkinter tanpa duplikasi kode."""

    def __init__(
        self,
        label: str,
        rel_x: float,
        rel_y: float,
        rel_w: float,
        rel_h: float,
        tag: str,
        page: int = 0
    ):
        self.label = label
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.rel_w = rel_w
        self.rel_h = rel_h
        self.tag = tag
        self.page = page

        # Canvas item IDs: [rect_border, label_banner, text_label, resize_handle]
        self.item_ids: Optional[List[int]] = None

    @property
    def display_text(self) -> str:
        """Teks label visual di canvas dengan indikator halaman jika bukan halaman 1."""
        if self.page == -1:
            return f"{self.label} [Hal Akhir]"
        elif self.page > 0:
            return f"{self.label} [Hal {self.page + 1}]"
        return self.label

    def calculate_pixels(self, canvas_w: float, canvas_h: float):
        """Menghitung koordinat pixel absolut dari koordinat relatif."""
        vx = self.rel_x * canvas_w
        vy = self.rel_y * canvas_h
        vw = self.rel_w * canvas_w
        vh = self.rel_h * canvas_h
        return vx, vy, vw, vh

    def draw(self, canvas: tk.Canvas, canvas_w: float, canvas_h: float, is_selected: bool = False) -> None:
        """Menggambar elemen visual kotak pada canvas pertama kali."""
        self.delete(canvas)

        vx, vy, vw, vh = self.calculate_pixels(canvas_w, canvas_h)
        outline_color = COLOR_WARNING if is_selected else ARC_BLUE

        r = canvas.create_rectangle(
            vx, vy, vx + vw, vy + vh,
            outline=outline_color, width=3, tags=(self.tag, "ui")
        )
        l = canvas.create_rectangle(
            vx, vy - 20, vx + vw, vy,
            fill=ARC_BLUE, tags=(self.tag, "ui")
        )
        t = canvas.create_text(
            vx + 5, vy - 10,
            text=self.display_text, fill="white", anchor="w",
            font=("Arial", 8, "bold"), tags=(self.tag, "ui")
        )
        h = canvas.create_rectangle(
            vx + vw - HANDLE_SIZE, vy + vh - HANDLE_SIZE, vx + vw, vy + vh,
            fill=ARC_BLUE, tags=(self.tag, "ui", "handle")
        )

        self.item_ids = [r, l, t, h]

    def update_coords(self, canvas: tk.Canvas, canvas_w: float, canvas_h: float) -> None:
        """Memperbarui koordinat seluruh elemen visual yang sudah ada di canvas."""
        if not self.item_ids or len(self.item_ids) < 4:
            self.draw(canvas, canvas_w, canvas_h)
            return

        vx, vy, vw, vh = self.calculate_pixels(canvas_w, canvas_h)
        r, l, t, h = self.item_ids

        canvas.coords(r, vx, vy, vx + vw, vy + vh)
        canvas.coords(l, vx, vy - 20, vx + vw, vy)
        canvas.coords(t, vx + 5, vy - 10)
        canvas.coords(h, vx + vw - HANDLE_SIZE, vy + vh - HANDLE_SIZE, vx + vw, vy + vh)

    def set_selection(self, canvas: tk.Canvas, is_selected: bool) -> None:
        """Mengubah warna outline ketika kotak dipilih atau tidak dipilih."""
        if self.item_ids:
            outline_color = COLOR_WARNING if is_selected else ARC_BLUE
            canvas.itemconfig(self.item_ids[0], outline=outline_color)

    def set_label(self, canvas: tk.Canvas, new_label: str) -> None:
        """Memperbarui label teks kotak."""
        self.label = new_label
        if self.item_ids and len(self.item_ids) >= 3:
            canvas.itemconfig(self.item_ids[2], text=self.display_text)

    def delete(self, canvas: tk.Canvas) -> None:
        """Menghapus seluruh item kotak dari canvas."""
        if self.item_ids:
            for item_id in self.item_ids:
                canvas.delete(item_id)
            self.item_ids = None

    def to_config(self) -> SignatureConfig:
        """Mengonversi ke model data konfigurasi."""
        return SignatureConfig(
            label=self.label,
            rel_x=self.rel_x,
            rel_y=self.rel_y,
            rel_w=self.rel_w,
            rel_h=self.rel_h,
            page=self.page
        )
