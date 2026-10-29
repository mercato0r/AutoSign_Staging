"""Pengujian unit khusus untuk memverifikasi optimasi arsitektur Python."""

import time
import unittest
from unittest.mock import MagicMock
from autosign.models import ProcessingTask, Profile, SignatureConfig, ProcessResult
from autosign.services.batch_orchestrator import BatchOrchestrator
from autosign.services.pdf_engine import PdfSignEngine


class TestArchitectureOptimizations(unittest.TestCase):

    def test_batch_orchestrator_progress_throttling(self):
        """Memverifikasi bahwa BatchOrchestrator membatasi frekuensi progress update agar tidak membanjiri UI."""
        progress_calls = []

        def on_progress(completed: int, total: int, speed: float, eta: str):
            progress_calls.append((completed, total))

        orchestrator = BatchOrchestrator(
            on_progress=on_progress,
            max_workers=2
        )

        # Mock PdfSignEngine.process_task agar selesai instan tanpa beban I/O
        orig_process = PdfSignEngine.process_task
        try:
            PdfSignEngine.process_task = MagicMock(
                return_value=ProcessResult(success=True)
            )

            # Buat 50 tugas instan
            dummy_profile = Profile(name="P", keywords=["K"], signatures=[])
            tasks = [
                ProcessingTask(
                    pdf_path=f"doc_{i}.pdf",
                    save_path=f"out_{i}.pdf",
                    profile=dummy_profile,
                    ttd_root="ttd",
                    rel_path=f"doc_{i}.pdf"
                )
                for i in range(50)
            ]

            orchestrator.execute_batch(tasks)

            # Sinyal progress tidak boleh terpanggil sebanyak 50 kali (karena terkena throttle 80ms)
            # tetapi tugas terakhir (50/50) harus SELALU terkirim
            self.assertLess(len(progress_calls), 50, "Progress update harus ter-throttle dan tidak 50 kali")
            self.assertGreaterEqual(len(progress_calls), 1, "Harus ada minimal 1 panggilan progress")
            # Pastikan progress terakhir merepresentasikan penyelesaian total
            last_completed, last_total = progress_calls[-1]
            self.assertEqual(last_completed, 50)
            self.assertEqual(last_total, 50)
        finally:
            PdfSignEngine.process_task = orig_process


if __name__ == "__main__":
    unittest.main()
