"""Orkestrator concurrency pemrosesan batch dokumen PDF."""

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Optional, Dict

from autosign.models import ProcessingTask, ProcessResult
from autosign.services.pdf_engine import PdfSignEngine
from autosign.services.metrics_tracker import MetricsTracker
from autosign.services.logger import get_logger


class BatchOrchestrator:
    """Mengelola thread pool dan eksekusi paralel tugas-tugas penandatanganan PDF."""

    def __init__(
        self,
        on_progress: Optional[Callable[[int, int, float, str], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[int, int], None]] = None,
        max_workers: Optional[int] = None
    ):
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_finished = on_finished
        self.stop_event = threading.Event()
        self.max_workers = max_workers or min(8, (os.cpu_count() or 1) + 1)
        self.metrics = MetricsTracker()
        self.logger = get_logger()

    def _log(self, message: str) -> None:
        self.logger.info(message)
        if self.on_log:
            self.on_log(message)

    def stop(self) -> None:
        """Mengirim sinyal pembatalan ke seluruh worker thread."""
        self.stop_event.set()
        self._log("🛑 Sinyal berhenti dikirim...")

    def execute_batch(self, tasks: List[ProcessingTask]) -> None:
        """Menjalankan batch tasks di thread latar belakang."""
        self.stop_event.clear()
        self.metrics.reset()

        success_count = 0
        failed_count = 0
        total_tasks = len(tasks)

        image_cache: Dict[str, bytes] = {}
        cache_lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    PdfSignEngine.process_task,
                    task,
                    image_cache,
                    cache_lock,
                    self.stop_event
                ): task
                for task in tasks
            }

            last_progress_time = 0.0
            for i, future in enumerate(as_completed(futures)):
                if self.stop_event.is_set():
                    break

                result: ProcessResult = future.result()
                if result.success:
                    success_count += 1
                else:
                    failed_count += 1
                    if result.error_message:
                        self._log(result.error_message)

                completed = i + 1
                now = time.time()
                is_last = (completed == total_tasks)

                # Batasi frekuensi sinyal UI progress (maksimal ~12.5 FPS / tiap 80ms) kecuali task terakhir
                if is_last or (now - last_progress_time >= 0.08):
                    last_progress_time = now
                    speed, eta = self.metrics.calculate_progress(completed, total_tasks)
                    if self.on_progress:
                        self.on_progress(completed, total_tasks, speed, eta)

        self._log(f"🏁 Selesai. Sukses: {success_count}, Gagal: {failed_count}")

        if self.on_finished:
            self.on_finished(success_count, failed_count)
