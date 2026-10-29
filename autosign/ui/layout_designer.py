"""Visual Layout Designer untuk menentukan penempatan tanda tangan pada PDF."""

import os
import threading
from typing import Optional, List, Callable
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import fitz
import customtkinter as ctk

from autosign.constants import (
    ARC_BLUE, BG_PANEL, COLOR_ORANGE, COLOR_WARNING,
    COLOR_DANGER, COLOR_SUCCESS, DEFAULT_BUTTON_STYLE, DragMode
)
from autosign.models import Profile, SignatureConfig
from autosign.services.profile_service import ProfileService
from autosign.ui.canvas_box import CanvasSignatureBox
from autosign.ui.tooltip import ToolTip


class LayoutDesigner(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        callback_save: Optional[Callable[[], None]] = None,
        edit_profile: Optional[Profile] = None,
        initial_pdf: Optional[str] = None,
        profile_service: Optional[ProfileService] = None
    ):
        super().__init__(parent)
        self.title("AutoSign - Layout Designer")
        self.geometry("1020x720")

        self.grab_set()
        self.focus_force()
        self.after(200, self._maximize_window)

        self.parent = parent
        self.callback_save = callback_save
        self.profile_service = profile_service or ProfileService()

        self.bg_photo: Optional[ImageTk.PhotoImage] = None
        self.boxes: List[CanvasSignatureBox] = []
        self.selected_idx: Optional[int] = None
        self.canvas_w: float = 1.0
        self.canvas_h: float = 1.0

        self.drag_mode = DragMode.NONE
        self.off_x: float = 0.0
        self.off_y: float = 0.0

        self.current_pdf_path = initial_pdf
        self.zoom_scale = 0.6
        self.current_page = 0
        self.total_pages = 1

        # Optimasi performa render asynchronous & debouncing
        self._zoom_debounce_timer: Optional[str] = None
        self._render_generation: int = 0
        self.bg_image_id: Optional[int] = None

        # History Stacks for Undo/Redo
        self.undo_stack: List[List[SignatureConfig]] = []
        self.redo_stack: List[List[SignatureConfig]] = []
        self._is_dragging: bool = False

        # Form variables
        default_name = edit_profile.name if edit_profile else "New_Profile"
        default_keys = ", ".join(edit_profile.keywords) if edit_profile else "KARTIR"
        self.profile_name = ctk.StringVar(value=default_name)
        self.keywords_raw = ctk.StringVar(value=default_keys)

        self._setup_ui()

        # Inisialisasi kotak tanda tangan jika dalam mode edit
        if edit_profile:
            for s in edit_profile.signatures:
                tag = f"box_{len(self.boxes)}"
                box = CanvasSignatureBox(
                    label=s.label,
                    rel_x=s.rel_x,
                    rel_y=s.rel_y,
                    rel_w=s.rel_w,
                    rel_h=s.rel_h,
                    tag=tag,
                    page=s.page
                )
                self.boxes.append(box)

        if self.current_pdf_path:
            self.after(500, self.render_pdf)

    def _maximize_window(self) -> None:
        try:
            self.state("zoomed")
        except tk.TclError:
            pass

    def _setup_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar Panel
        sidebar = ctk.CTkFrame(self, width=290, corner_radius=0, fg_color=BG_PANEL)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="LAYOUT SETTINGS",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))

        ctk.CTkLabel(sidebar, text="Profile Name:", anchor="w").pack(fill="x", padx=20)
        ctk.CTkEntry(sidebar, textvariable=self.profile_name).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(sidebar, text="Keywords (Comma separated):", anchor="w").pack(fill="x", padx=20)
        ctk.CTkEntry(sidebar, textvariable=self.keywords_raw).pack(fill="x", padx=20, pady=(0, 15))

        self.btn_load_sample = ctk.CTkButton(
            sidebar, text="📂 Buka PDF Contoh",
            command=self.load_sample, **DEFAULT_BUTTON_STYLE
        )
        self.btn_load_sample.pack(fill="x", padx=20, pady=(5, 5))
        ToolTip(self.btn_load_sample, "Buka file PDF contoh untuk panduan tata letak")

        # Page Navigation Controls
        page_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        page_frame.pack(fill="x", padx=20, pady=5)
        self.btn_prev_page = ctk.CTkButton(
            page_frame, text="◀", width=35, command=self.prev_page, **DEFAULT_BUTTON_STYLE
        )
        self.btn_prev_page.pack(side="left")
        ToolTip(self.btn_prev_page, "Pindah ke halaman sebelumnya")

        self.lbl_page_info = ctk.CTkLabel(
            page_frame, text="Hal: 1 / 1", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_page_info.pack(side="left", expand=True)

        self.btn_next_page = ctk.CTkButton(
            page_frame, text="▶", width=35, command=self.next_page, **DEFAULT_BUTTON_STYLE
        )
        self.btn_next_page.pack(side="right")
        ToolTip(self.btn_next_page, "Pindah ke halaman berikutnya")

        # Zoom Controls
        zoom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        zoom_frame.pack(fill="x", padx=20, pady=5)
        self.btn_zoom_in = ctk.CTkButton(
            zoom_frame, text="🔍⁺",
            command=lambda: self.adjust_zoom(0.1, immediate=True), width=10, **DEFAULT_BUTTON_STYLE
        )
        self.btn_zoom_in.pack(side="left", expand=True, padx=2)
        ToolTip(self.btn_zoom_in, "Perbesar tampilan PDF (Ctrl + Scroll Up)")

        self.btn_zoom_out = ctk.CTkButton(
            zoom_frame, text="🔍⁻",
            command=lambda: self.adjust_zoom(-0.1, immediate=True), width=10, **DEFAULT_BUTTON_STYLE
        )
        self.btn_zoom_out.pack(side="right", expand=True, padx=2)
        ToolTip(self.btn_zoom_out, "Perkecil tampilan PDF (Ctrl + Scroll Down)")

        # Undo / Redo Controls
        history_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        history_frame.pack(fill="x", padx=20, pady=5)
        self.btn_undo = ctk.CTkButton(
            history_frame, text="↩",
            command=self.undo, width=10, **DEFAULT_BUTTON_STYLE
        )
        self.btn_undo.pack(side="left", expand=True, padx=2)
        ToolTip(self.btn_undo, "Batalkan aksi terakhir (Ctrl+Z)")

        self.btn_redo = ctk.CTkButton(
            history_frame, text="↪",
            command=self.redo, width=10, **DEFAULT_BUTTON_STYLE
        )
        self.btn_redo.pack(side="right", expand=True, padx=2)
        ToolTip(self.btn_redo, "Ulangi aksi yang dibatalkan (Ctrl+Y)")

        # Action Buttons
        self.btn_add_box = ctk.CTkButton(
            sidebar, text="➕ Kotak Baru",
            command=self.add_box, fg_color=COLOR_ORANGE, **DEFAULT_BUTTON_STYLE
        )
        self.btn_add_box.pack(fill="x", padx=20, pady=(15, 5))
        ToolTip(self.btn_add_box, "Tambah area tanda tangan baru")

        # Row untuk tombol aksi edit & hapus agar lebih ringkas dan hemat ruang
        box_action_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        box_action_frame.pack(fill="x", padx=20, pady=5)

        self.btn_edit_label = ctk.CTkButton(
            box_action_frame, text="✏️ Label",
            command=self.edit_box_label, fg_color=COLOR_WARNING, **DEFAULT_BUTTON_STYLE
        )
        self.btn_edit_label.pack(side="left", expand=True, padx=(0, 2))
        ToolTip(self.btn_edit_label, "Ubah nama label kotak tanda tangan yang dipilih")

        self.btn_delete_box = ctk.CTkButton(
            box_action_frame, text="🗑️ Hapus",
            command=self.delete_box, fg_color=COLOR_DANGER, **DEFAULT_BUTTON_STYLE
        )
        self.btn_delete_box.pack(side="right", expand=True, padx=(2, 0))
        ToolTip(self.btn_delete_box, "Hapus kotak tanda tangan yang dipilih")

        self.btn_save = ctk.CTkButton(
            sidebar, text="💾 Simpan Profil",
            command=self.save_profile, fg_color=COLOR_SUCCESS, height=45
        )
        self.btn_save.pack(fill="x", padx=20, side="bottom", pady=20)
        ToolTip(self.btn_save, "Simpan seluruh tata letak tanda tangan ke profil")

        # Canvas Preview
        self.canvas = tk.Canvas(self, bg="gray50", highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Panning bindings: Middle-Click (Button-2) dan Right-Click (Button-3)
        self.canvas.bind("<ButtonPress-2>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B2-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind("<ButtonPress-3>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B3-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))

        # Zoom binding dengan debouncing halus saat scroll mouse
        self.canvas.bind(
            "<Control-MouseWheel>",
            lambda e: self.adjust_zoom(0.1 if e.delta > 0 else -0.1, immediate=False)
        )

        # Keyboard shortcuts untuk Undo / Redo
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-Z>", lambda e: self.redo())

    def prev_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            if self._zoom_debounce_timer:
                self.after_cancel(self._zoom_debounce_timer)
                self._zoom_debounce_timer = None
            self.render_pdf()

    def next_page(self) -> None:
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            if self._zoom_debounce_timer:
                self.after_cancel(self._zoom_debounce_timer)
                self._zoom_debounce_timer = None
            self.render_pdf()

    def load_sample(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.current_pdf_path = path
            self.current_page = 0
            if hasattr(self.parent, "last_designer_pdf"):
                self.parent.last_designer_pdf = path
            if self._zoom_debounce_timer:
                self.after_cancel(self._zoom_debounce_timer)
                self._zoom_debounce_timer = None
            self.bg_image_id = None
            self.render_pdf()

    def _is_box_on_active_page(self, box: CanvasSignatureBox) -> bool:
        """Mengecek apakah kotak berada pada halaman yang sedang aktif."""
        if box.page == -1:
            return self.current_page == self.total_pages - 1
        return box.page == self.current_page

    def render_pdf(self) -> None:
        """Merender halaman aktif PDF ke canvas secara asynchronous di background thread."""
        if not self.current_pdf_path or not os.path.exists(self.current_pdf_path):
            return

        self._render_generation += 1
        current_gen = self._render_generation
        target_path = self.current_pdf_path
        target_page = self.current_page
        target_zoom = self.zoom_scale

        def worker():
            try:
                with fitz.open(target_path) as doc:
                    total_pages = len(doc)
                    if total_pages == 0:
                        self.after(0, lambda: messagebox.showwarning("Peringatan", "File PDF tidak memiliki halaman."))
                        return

                    page_idx = target_page
                    if page_idx >= total_pages:
                        page_idx = max(0, total_pages - 1)

                    page = doc[page_idx]
                    pix = page.get_pixmap(matrix=fitz.Matrix(target_zoom, target_zoom))
                    w, h = pix.width, pix.height
                    samples = pix.samples
                    self.after(
                        0,
                        self._apply_rendered_pixmap,
                        current_gen,
                        w,
                        h,
                        samples,
                        total_pages,
                        page_idx
                    )
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error", f"Gagal merender PDF:\n{err}"))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_rendered_pixmap(
        self,
        generation: int,
        width: int,
        height: int,
        samples: bytes,
        total_pages: int,
        resolved_page_idx: int
    ) -> None:
        """Menerapkan pixmap hasil render background ke canvas di Main UI Thread."""
        # Jika ada pemanggilan render yang lebih baru, abaikan hasil yang sudah usang
        if generation != self._render_generation:
            return

        self.total_pages = total_pages
        self.current_page = resolved_page_idx
        self.lbl_page_info.configure(text=f"Hal: {self.current_page + 1} / {self.total_pages}")

        self.canvas_w, self.canvas_h = float(width), float(height)
        img = Image.frombytes("RGB", [width, height], samples)
        self.bg_photo = ImageTk.PhotoImage(img)

        # Update atau buat image background tanpa menghancurkan seluruh canvas jika memungkinkan
        if self.bg_image_id is None or not self.canvas.find_withtag("bg_pdf"):
            self.canvas.delete("all")
            self.bg_image_id = self.canvas.create_image(
                0, 0, anchor="nw", image=self.bg_photo, tags="bg_pdf"
            )
            for box in self.boxes:
                if self._is_box_on_active_page(box):
                    box.draw(self.canvas, self.canvas_w, self.canvas_h)
        else:
            self.canvas.itemconfig(self.bg_image_id, image=self.bg_photo)
            for box in self.boxes:
                if self._is_box_on_active_page(box):
                    if box.item_ids and self.canvas.find_withtag(box.tag):
                        box.update_coords(self.canvas, self.canvas_w, self.canvas_h)
                    else:
                        box.draw(self.canvas, self.canvas_w, self.canvas_h)
                else:
                    box.delete(self.canvas)

        self.canvas.config(scrollregion=(0, 0, self.canvas_w, self.canvas_h))

    def adjust_zoom(self, delta: float, immediate: bool = False) -> None:
        """Mengatur skala zoom canvas dengan aman antara 0.2 hingga 2.5 dengan debouncing."""
        new_scale = max(0.2, min(2.5, round(self.zoom_scale + delta, 2)))
        if new_scale != self.zoom_scale:
            self.zoom_scale = new_scale
            if immediate:
                if self._zoom_debounce_timer:
                    self.after_cancel(self._zoom_debounce_timer)
                    self._zoom_debounce_timer = None
                self.render_pdf()
            else:
                if self._zoom_debounce_timer:
                    self.after_cancel(self._zoom_debounce_timer)
                self._zoom_debounce_timer = self.after(100, self.render_pdf)

    def _snapshot_state(self) -> List[SignatureConfig]:
        """Membuat snapshot list konfigurasi kotak tanda tangan saat ini."""
        return [box.to_config() for box in self.boxes]

    def _push_undo(self, snapshot: Optional[List[SignatureConfig]] = None) -> None:
        """Menyimpan snapshot ke undo stack dan mengosongkan redo stack."""
        state = snapshot if snapshot is not None else self._snapshot_state()
        self.undo_stack.append(state)
        if len(self.undo_stack) > 30:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _restore_state(self, state: List[SignatureConfig]) -> None:
        """Merestorasi susunan kotak tanda tangan dari snapshot."""
        # Bersihkan elemen visual kotak lama dari canvas
        for box in self.boxes:
            box.delete(self.canvas)
        self.boxes.clear()
        self.selected_idx = None
        self.drag_mode = DragMode.NONE

        for s in state:
            tag = f"box_{len(self.boxes)}"
            box = CanvasSignatureBox(
                label=s.label,
                rel_x=s.rel_x,
                rel_y=s.rel_y,
                rel_w=s.rel_w,
                rel_h=s.rel_h,
                tag=tag,
                page=s.page
            )
            self.boxes.append(box)
            if self._is_box_on_active_page(box):
                box.draw(self.canvas, self.canvas_w, self.canvas_h)

    def undo(self) -> None:
        """Membatalkan aksi perubahan terakhir."""
        if not self.undo_stack:
            return
        current_state = self._snapshot_state()
        self.redo_stack.append(current_state)
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)

    def redo(self) -> None:
        """Mengulang aksi yang sebelumnya dibatalkan."""
        if not self.redo_stack:
            return
        current_state = self._snapshot_state()
        self.undo_stack.append(current_state)
        next_state = self.redo_stack.pop()
        self._restore_state(next_state)

    def add_box(self) -> None:
        """Menambahkan kotak tanda tangan baru menggunakan CustomTkinter Input Dialog."""
        dialog = ctk.CTkInputDialog(
            title="Label Tanda Tangan",
            text="Nama file gambar tanda tangan (tanpa .png):"
        )
        label = dialog.get_input()
        if not label or not label.strip():
            return
        label = label.strip()

        # Simpan state sebelum menambah kotak
        self._push_undo()

        try:
            cx = self.canvas.canvasx(self.canvas.winfo_width() / 2)
            cy = self.canvas.canvasy(self.canvas.winfo_height() / 2)
            rx = max(0.0, min(cx / max(1.0, self.canvas_w), 0.85))
            ry = max(0.0, min(cy / max(1.0, self.canvas_h), 0.92))
        except Exception:
            rx, ry = 0.1, 0.1

        tag = f"box_{len(self.boxes)}"
        new_box = CanvasSignatureBox(
            label=label,
            rel_x=rx,
            rel_y=ry,
            rel_w=0.15,
            rel_h=0.08,
            tag=tag,
            page=self.current_page
        )
        self.boxes.append(new_box)
        new_box.draw(self.canvas, self.canvas_w, self.canvas_h)

    def edit_box_label(self) -> None:
        """Mengedit label kotak tanda tangan yang sedang dipilih."""
        if self.selected_idx is not None and self.selected_idx < len(self.boxes):
            box = self.boxes[self.selected_idx]
            dialog = ctk.CTkInputDialog(
                title="Edit Label",
                text=f"Nama file tanda tangan baru (saat ini: {box.label}):"
            )
            new_label = dialog.get_input()
            if new_label and new_label.strip() and new_label.strip() != box.label:
                self._push_undo()
                box.set_label(self.canvas, new_label.strip())

    def on_click(self, event) -> None:
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(cx, cy)
        tags = self.canvas.gettags(item)

        self.selected_idx = None
        self.drag_mode = DragMode.NONE
        self._drag_start_snapshot = None

        if "ui" in tags:
            for idx, box in enumerate(self.boxes):
                if box.tag in tags and self._is_box_on_active_page(box):
                    self.selected_idx = idx
                    self._drag_start_snapshot = self._snapshot_state()
                    if "handle" in tags:
                        self.drag_mode = DragMode.RESIZE
                    else:
                        self.drag_mode = DragMode.MOVE
                    self.off_x = cx - (box.rel_x * self.canvas_w)
                    self.off_y = cy - (box.rel_y * self.canvas_h)
                    break

        for idx, box in enumerate(self.boxes):
            if self._is_box_on_active_page(box):
                box.set_selection(self.canvas, idx == self.selected_idx)

    def on_move(self, event) -> None:
        if self.selected_idx is None or self.selected_idx >= len(self.boxes):
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        box = self.boxes[self.selected_idx]

        if not self._is_box_on_active_page(box):
            return

        if self.drag_mode == DragMode.RESIZE:
            box.rel_w = max(0.01, (cx - (box.rel_x * self.canvas_w)) / self.canvas_w)
            box.rel_h = max(0.01, (cy - (box.rel_y * self.canvas_h)) / self.canvas_h)
        elif self.drag_mode == DragMode.MOVE:
            box.rel_x = (cx - self.off_x) / self.canvas_w
            box.rel_y = (cy - self.off_y) / self.canvas_h

        box.update_coords(self.canvas, self.canvas_w, self.canvas_h)

    def on_release(self, _event) -> None:
        """Mencatat perubahan ke history undo saat selesai drag/resize."""
        if hasattr(self, "_drag_start_snapshot") and self._drag_start_snapshot:
            current = self._snapshot_state()
            # Catat jika ada perubahan posisi atau ukuran
            if current != self._drag_start_snapshot:
                self._push_undo(self._drag_start_snapshot)
            self._drag_start_snapshot = None

    def delete_box(self) -> None:
        if self.selected_idx is not None and self.selected_idx < len(self.boxes):
            self._push_undo()
            box = self.boxes.pop(self.selected_idx)
            box.delete(self.canvas)
            self.selected_idx = None

    def save_profile(self) -> None:
        name = self.profile_name.get().strip()
        keywords = [k.strip() for k in self.keywords_raw.get().split(",") if k.strip()]

        if not name:
            messagebox.showwarning("Peringatan", "Nama profil tidak boleh kosong!", parent=self)
            return
        if not self.boxes:
            messagebox.showwarning("Peringatan", "Tambahkan minimal satu kotak tanda tangan!", parent=self)
            return

        profile = Profile(
            name=name,
            keywords=keywords,
            signatures=[box.to_config() for box in self.boxes]
        )

        self.profile_service.save_profile(profile)

        if self.callback_save:
            self.callback_save()
        self.destroy()
