"""Layanan kalkulasi throughput kecepatan pemrosesan dan estimasi waktu selesai (ETA)."""

import time
import datetime
from typing import Tuple


class MetricsTracker:
    def __init__(self):
        self.start_time: float = time.time()

    def reset(self) -> None:
        """Mereset stopwatch."""
        self.start_time = time.time()

    def calculate_progress(self, completed: int, total: int) -> Tuple[float, str]:
        """
        Menghitung kecepatan pemrosesan file per detik dan format teks ETA.
        Mengembalikan tuple: (speed_fps, eta_string).
        """
        elapsed = time.time() - self.start_time
        speed = completed / elapsed if elapsed > 0 else 0.0

        if speed > 0 and total > completed:
            remaining_seconds = int((total - completed) / speed)
            eta_str = str(datetime.timedelta(seconds=remaining_seconds))
        else:
            eta_str = "..."

        return speed, eta_str
