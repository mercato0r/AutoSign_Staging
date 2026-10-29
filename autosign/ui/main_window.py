"""Jendela Utama (Main Window) aplikasi AutoSign Pro yang bersih tanpa God Object."""

import os
import threading
import datetime
from typing import Dict, Tuple, List, Optional
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from autosign.constants import (
    ARC_BLUE, BG_PANEL, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_WARNING, COLOR_SECONDARY, COLOR_INFO,
    COLOR_LOG_TEXT, COLOR_LOG_BG
)
from autosign.models import Profile, AppSettings, ProcessingTask
from autosign.services.settings_service import SettingsService
from autosign.services.profile_service import ProfileService
from autosign.services.batch_scanner import BatchScanner
from autosign.services.batch_orchestrator import BatchOrchestrator
from autosign.services.logger import setup_logger, register_ui_log_callback, get_logger
from autosign.ui.layout_designer import LayoutDesigner
from autosign.ui.profile_row import ProfileRowItem


class MainWindow(ctk.CTk):
    """Jendela utama AutoSign yang bertindak murni sebagai GUI Presenter/View."""

    def __init__(self):
        super().__init__()
        self.title("AutoSign Pro")
        self.geometry("920x860")

        # Inisialisasi Sistem Logging Terpusat
        self.logger = setup_logger()
        register_ui_log_callback(self._log_message)

        # Inisialisasi Layanan Backend (Inversion of Control)
        self.settings_service = SettingsService()
        self.profile_service = ProfileService()
        self.batch_orchestrator = BatchOrchestrator(
            on_progress=self._on_worker_progress,
            on_log=self._log_message,
            on_finished=self._on_worker_finished
        )

        # UI State Variables
        self.pdf_root = ctk.StringVar()
        self.ttd_master = ctk.StringVar()
        self.output_dir = ctk.StringVar()
        self.skip_processed = ctk.BooleanVar(value=True)

        # Buffer & throttling untuk log window
        self._log_buffer: List[str] = []
        self._log_lock = threading.Lock()
        self._log_flush_pending = False

        self.profile_items: Dict[str, Tuple[ctk.BooleanVar, Profile]] = {}
        self.last_designer_pdf: Optional[str] = None

        self._setup_ui()
        self._load_saved_settings()
        self.refresh_profiles()

    def _setup_ui(self) -> None:
        """Menyusun seluruh komponen antarmuka pengguna."""
        # 1. HEADER PANEL
        header = ctk.CTkFrame(self, corner_radius=0, height=70, fg_color=BG_PANEL)
        header.pack(fill="x", side="top")

        ctk.CTkLabel(
            header, text="AUTOSIGN PRO",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ARC_BLUE
        ).pack(side="left", padx=30)

        self.theme_menu = ctk.CTkOptionMenu(
            header, values=["Dark", "Light"],
            command=self._change_appearance_mode, width=100
        )
        self.theme_menu.pack(side="right", padx=30)
        self.theme_menu.set("Dark")

        # 2. FOOTER PANEL
        footer = ctk.CTkFrame(self, corner_radius=0, height=130, fg_color=BG_PANEL)
        footer.pack(fill="x", side="bottom")

        self.lbl_status = ctk.CTkLabel(footer, text="Ready.", font=("Arial", 12))
        self.lbl_status.pack(anchor="w", padx=30, pady=(10, 0))

        self.progress_bar = ctk.CTkProgressBar(footer, height=10)
        self.progress_bar.pack(fill="x", padx=30, pady=10)
        self.progress_bar.set(0)

        button_row = ctk.CTkFrame(footer, fg_color="transparent")
        button_row.pack(fill="x", padx=30, pady=(0, 10))

        self.btn_run = ctk.CTkButton(
            button_row, text="🚀 RUN PROCESS",
            command=self.start_process, fg_color=COLOR_SUCCESS,
            height=40, font=("Arial", 13, "bold")
        )
        self.btn_run.pack(side="left", expand=True, padx=(0, 5))

        self.btn_stop = ctk.CTkButton(
            button_row, text="🛑 STOP",
            command=self.stop_process, fg_color=COLOR_DANGER,
            height=40, state="disabled"
        )
        self.btn_stop.pack(side="left", expand=True, padx=5)

        self.btn_open_out = ctk.CTkButton(
            button_row, text="📂 OPEN OUTPUT",
            command=self.open_output_folder, fg_color=COLOR_INFO,
            height=40, state="disabled"
        )
        self.btn_open_out.pack(side="left", expand=True, padx=(5, 0))

        # 3. SCROLLABLE MAIN BODY
        main_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        # Bagian 1: Manajemen Profil
        ctk.CTkLabel(
            main_body, text="📜 Profile Management",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(10, 5))

        profile_ctrl_row = ctk.CTkFrame(main_body, fg_color="transparent")
        profile_ctrl_row.pack(fill="x", pady=(0, 5))

        self.lbl_profile_count = ctk.CTkLabel(
            profile_ctrl_row, text="(0/0 Selected)",
            text_color=COLOR_WARNING, font=("Arial", 12, "bold")
        )
        self.lbl_profile_count.pack(side="left")

        ctk.CTkButton(
            profile_ctrl_row, text="☑ Toggle All",
            width=90, height=26, fg_color=COLOR_SECONDARY,
            command=self.toggle_select_all
        ).pack(side="right")

        self.scroll_profiles = ctk.CTkScrollableFrame(main_body, height=200, border_width=1)
        self.scroll_profiles.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            main_body, text="➕ Create New Profile",
            command=self._open_new_designer
        ).pack(fill="x", pady=(0, 25))

        # Bagian 2: Konfigurasi Path
        ctk.CTkLabel(
            main_body, text="📂 Path Configuration",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=(10, 5))

        path_frame = ctk.CTkFrame(main_body, border_width=1, corner_radius=8)
        path_frame.pack(fill="x", pady=(0, 15))
        path_frame.columnconfigure(1, weight=1)

        self._create_path_row(path_frame, "PDF Master:", self.pdf_root, 0)
        self._create_path_row(path_frame, "Signature Master:", self.ttd_master, 1)
        self._create_path_row(path_frame, "Output Folder:", self.output_dir, 2)

        # Bagian 3: Opsi & Terminal Log
        ctk.CTkCheckBox(
            main_body, text="Skip existing files (Efficiency)",
            variable=self.skip_processed
        ).pack(anchor="w", pady=(0, 15))

        self.log_box = ctk.CTkTextbox(
            main_body, height=180, font=("Consolas", 12),
            text_color=COLOR_LOG_TEXT, fg_color=COLOR_LOG_BG
        )
        self.log_box.pack(fill="x", pady=(0, 10))
        self.log_box.configure(state="disabled")

    def _change_appearance_mode(self, new_mode: str) -> None:
        ctk.set_appearance_mode(new_mode)

    def _create_path_row(self, parent: ctk.CTkFrame, label: str, var: ctk.StringVar, row_idx: int) -> None:
        ctk.CTkLabel(parent, text=label, width=130, anchor="w").grid(row=row_idx, column=0, padx=15, pady=10)
        ctk.CTkEntry(parent, textvariable=var).grid(row=row_idx, column=1, sticky="ew", padx=(0, 10))
        ctk.CTkButton(
            parent, text="Browse", width=70,
            command=lambda: self._browse_directory(var)
        ).grid(row=row_idx, column=2, padx=(0, 15))

    def _browse_directory(self, target_var: ctk.StringVar) -> None:
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            target_var.set(selected_dir)
            self._save_current_settings()

    def _log_message(self, message: str) -> None:
        """Mencatat pesan ke log box secara thread-safe dengan batch buffering."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        with self._log_lock:
            self._log_buffer.append(entry)
            if not self._log_flush_pending:
                self._log_flush_pending = True
                self.after(80, self._flush_log_buffer)

    def _flush_log_buffer(self) -> None:
        """Menulis akumulasi buffer log ke widget log_box sekaligus."""
        with self._log_lock:
            if not self._log_buffer:
                self._log_flush_pending = False
                return
            combined_text = "".join(self._log_buffer)
            self._log_buffer.clear()
            self._log_flush_pending = False

        try:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", combined_text)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        except Exception:
            pass

    def _load_saved_settings(self) -> None:
        settings = self.settings_service.load_settings()
        self.pdf_root.set(settings.pdf_root)
        self.ttd_master.set(settings.ttd_master)
        self.output_dir.set(settings.output_dir)

    def _save_current_settings(self) -> None:
        settings = AppSettings(
            pdf_root=self.pdf_root.get(),
            ttd_master=self.ttd_master.get(),
            output_dir=self.output_dir.get()
        )
        self.settings_service.save_settings(settings)

    def refresh_profiles(self) -> None:
        """Memuat ulang daftar profil dari ProfileService dan merender widget ProfileRowItem."""
        for widget in self.scroll_profiles.winfo_children():
            widget.destroy()

        self.profile_items.clear()
        profiles_list = self.profile_service.list_profiles()

        for filename, profile in profiles_list:
            var = ctk.BooleanVar(value=True)
            var.trace_add("write", lambda *args: self._update_profile_count_label())
            self.profile_items[filename] = (var, profile)

            item_row = ProfileRowItem(
                parent=self.scroll_profiles,
                filename=filename,
                profile=profile,
                is_selected_var=var,
                on_delete=self._delete_profile,
                on_copy=self._duplicate_profile,
                on_edit=self._open_edit_designer
            )
            item_row.pack(fill="x", pady=2)

        self._update_profile_count_label()

    def _delete_profile(self, filename: str, profile_name: str) -> None:
        if messagebox.askyesno("Delete", f"Delete profile '{profile_name}'?", parent=self):
            self.profile_service.delete_profile(filename)
            self.refresh_profiles()

    def _duplicate_profile(self, profile: Profile) -> None:
        self.profile_service.duplicate_profile(profile)
        self.refresh_profiles()

    def _open_new_designer(self) -> None:
        LayoutDesigner(
            parent=self,
            callback_save=self.refresh_profiles,
            initial_pdf=self.last_designer_pdf,
            profile_service=self.profile_service
        )

    def _open_edit_designer(self, profile: Profile) -> None:
        LayoutDesigner(
            parent=self,
            callback_save=self.refresh_profiles,
            edit_profile=profile,
            initial_pdf=self.last_designer_pdf,
            profile_service=self.profile_service
        )

    def toggle_select_all(self) -> None:
        new_state = not all(var.get() for var, _ in self.profile_items.values())
        for var, _ in self.profile_items.values():
            var.set(new_state)

    def _update_profile_count_label(self) -> None:
        selected_count = sum(1 for var, _ in self.profile_items.values() if var.get())
        total_count = len(self.profile_items)
        self.lbl_profile_count.configure(text=f"({selected_count}/{total_count} Selected)")

    def open_output_folder(self) -> None:
        out_path = self.output_dir.get()
        if os.path.exists(out_path):
            os.startfile(os.path.abspath(out_path))
        else:
            messagebox.showwarning("Peringatan", "Folder output belum tersedia.", parent=self)

    def start_process(self) -> None:
        """Memvalidasi input dan memulai pemindaian file latar belakang."""
        selected_profiles = [prof for var, prof in self.profile_items.values() if var.get()]
        pdf_root = self.pdf_root.get()
        ttd_root = self.ttd_master.get()
        output_dir = self.output_dir.get()

        if not selected_profiles or not all([pdf_root, ttd_root, output_dir]):
            messagebox.showwarning(
                "Peringatan",
                "Lengkapi input path dan pilih minimal 1 profil!",
                parent=self
            )
            return

        self.btn_run.configure(state="disabled", text="🔎 SCANNING...")
        self.btn_open_out.configure(state="disabled")

        # Pindai file di thread background agar GUI tidak membeku
        threading.Thread(
            target=self._scan_and_prepare_batch,
            args=(selected_profiles, pdf_root, ttd_root, output_dir),
            daemon=True
        ).start()

    def _scan_and_prepare_batch(
        self,
        profiles: List[Profile],
        pdf_root: str,
        ttd_root: str,
        output_dir: str
    ) -> None:
        self._log_message("🔎 Memulai pemindaian file...")

        tasks = BatchScanner.scan_files(
            pdf_root=pdf_root,
            ttd_root=ttd_root,
            output_dir=output_dir,
            profiles=profiles,
            skip_processed=self.skip_processed.get()
        )

        if not tasks:
            self._log_message("✅ Tidak ada file baru ditemukan.")
            self.after(0, self._reset_ui_state, 0, 0, False)
            return

        self.after(0, self._confirm_and_launch_batch, tasks)

    def _confirm_and_launch_batch(self, tasks: List[ProcessingTask]) -> None:
        message = f"Ditemukan {len(tasks)} file PDF yang cocok.\nLanjutkan proses?"
        if messagebox.askyesno("Konfirmasi", message, parent=self):
            self.btn_run.configure(text="⏳ PROCESSING...", state="disabled")
            self.btn_stop.configure(state="normal")

            threading.Thread(
                target=self.batch_orchestrator.execute_batch,
                args=(tasks,),
                daemon=True
            ).start()
        else:
            self._log_message("⚠ Dibatalkan.")
            self._reset_ui_state(0, 0, False)

    def stop_process(self) -> None:
        self.batch_orchestrator.stop()

    def _on_worker_progress(self, completed: int, total: int, speed: float, eta: str) -> None:
        def update():
            progress_ratio = completed / total if total > 0 else 0
            self.progress_bar.set(progress_ratio)
            self.lbl_status.configure(
                text=f"Prog: {completed}/{total} | Spd: {speed:.1f} f/s | ETA: {eta}"
            )
        self.after(0, update)

    def _on_worker_finished(self, success_count: int, failed_count: int) -> None:
        self.after(0, self._reset_ui_state, success_count, failed_count, True)

    def _reset_ui_state(self, success_count: int, failed_count: int, show_popup: bool) -> None:
        self._flush_log_buffer()
        self.btn_run.configure(state="normal", text="🚀 RUN PROCESS")
        self.btn_stop.configure(state="disabled")
        self.btn_open_out.configure(state="normal")
        self.progress_bar.set(0)
        self.lbl_status.configure(text="Ready.")

        if show_popup:
            messagebox.showinfo(
                "Proses Selesai",
                f"🏁 Ringkasan Proses:\n\n✅ Berhasil: {success_count}\n❌ Gagal: {failed_count}",
                parent=self
            )
