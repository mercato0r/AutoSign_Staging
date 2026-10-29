"""Engine manipulasi PDF independen untuk pembubuhan stempel dan tanda tangan."""

import os
import threading
from typing import Dict, Optional, Set
import fitz  # PyMuPDF
from autosign.models import ProcessingTask, ProcessResult
from autosign.services.signature_resolver import SignatureResolver
from autosign.services.logger import get_logger


class PdfSignEngine:
    """Engine murni untuk membubuhkan tanda tangan ke dokumen PDF tanpa ketergantungan GUI."""

    @staticmethod
    def process_task(
        task: ProcessingTask,
        cache: Dict[str, bytes],
        lock: threading.Lock,
        stop_event: Optional[threading.Event] = None
    ) -> ProcessResult:
        """
        Mengeksekusi penempelan tanda tangan pada satu dokumen PDF berdasarkan profil.
        Mendukung multi-halaman (page 0, page 1, ..., atau page -1 untuk halaman terakhir).
        Menggunakan in-memory cache thread-safe agar file gambar yang sama tidak dibaca berulang.
        """
        logger = get_logger()

        if stop_event and stop_event.is_set():
            return ProcessResult(success=False, error_message="Cancelled", task=task)

        try:
            # Pastikan folder penyimpanan output tersedia
            os.makedirs(os.path.dirname(task.save_path), exist_ok=True)

            with fitz.open(task.pdf_path) as doc:
                total_pages = len(doc)
                if total_pages == 0:
                    return ProcessResult(
                        success=False,
                        error_message=f"❌ ERR: {task.rel_path} -> Dokumen PDF kosong (0 halaman)",
                        task=task
                    )

                modified_pages: Set[int] = set()

                for sig in task.profile.signatures:
                    # Resolusi target halaman (mendukung indeks negatif seperti -1 untuk halaman terakhir)
                    target_idx = sig.page if sig.page >= 0 else total_pages + sig.page
                    if target_idx < 0 or target_idx >= total_pages:
                        target_idx = 0  # Fallback aman ke halaman pertama jika nomor halaman di luar batas

                    page = doc[target_idx]
                    modified_pages.add(target_idx)

                    page_rotation = page.rotation
                    pdf_w, pdf_h = page.rect.width, page.rect.height

                    # Konversi koordinat relatif ke ukuran PDF absolut
                    x = sig.rel_x * pdf_w
                    y = sig.rel_y * pdf_h
                    w = sig.rel_w * pdf_w
                    h = sig.rel_h * pdf_h

                    # Resolusi path gambar stempel
                    img_path = SignatureResolver.resolve(task.ttd_root, task.rel_path, sig.label)
                    if not img_path:
                        filename = f"{sig.label}.png"
                        doc_name = os.path.basename(task.pdf_path)
                        err_msg = f"❌ MISSING: {filename} untuk {doc_name}"
                        logger.warning(err_msg)
                        return ProcessResult(
                            success=False,
                            error_message=err_msg,
                            task=task
                        )

                    # Ambil binary gambar dari thread-safe cache
                    img_bytes = cache.get(img_path)
                    if not img_bytes:
                        with lock:
                            img_bytes = cache.get(img_path)
                            if not img_bytes:
                                with open(img_path, "rb") as f:
                                    img_bytes = f.read()
                                cache[img_path] = img_bytes

                    # Tempelkan gambar dengan matriks derotasi sesuai rotasi halaman
                    rect = fitz.Rect(x, y, x + w, y + h) * page.derotation_matrix
                    page.insert_image(
                        rect,
                        stream=img_bytes,
                        overlay=True,
                        rotate=page_rotation
                    )

                for page_idx in modified_pages:
                    doc[page_idx].clean_contents()

                doc.save(task.save_path, deflate=True)

            return ProcessResult(success=True, task=task)

        except Exception as e:
            err_msg = f"❌ ERR: {task.rel_path} -> {str(e)}"
            logger.error(err_msg)
            return ProcessResult(
                success=False,
                error_message=err_msg,
                task=task
            )
