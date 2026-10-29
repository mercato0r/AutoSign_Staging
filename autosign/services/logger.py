"""Sistem logging standar terpusat untuk AutoSign Pro."""

import logging
from logging.handlers import RotatingFileHandler
from typing import Callable, Optional, List

LOGGER_NAME = "autosign"
LOG_FILE = "autosign.log"

_ui_callbacks: List[Callable[[str], None]] = []


class UiLogHandler(logging.Handler):
    """Handler custom untuk meneruskan log ke UI callback secara aman."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            for cb in _ui_callbacks:
                try:
                    cb(msg)
                except Exception:
                    pass
        except Exception:
            self.handleError(record)


def setup_logger(log_file: str = LOG_FILE) -> logging.Logger:
    """Menginisialisasi logger standar dengan rotasi file dan handler antarmuka."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 1. Rotating File Handler (Max 2MB per file, simpan 3 backup)
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass

    # 2. UI Stream Handler
    ui_handler = UiLogHandler()
    ui_formatter = logging.Formatter("%(message)s")
    ui_handler.setFormatter(ui_formatter)
    logger.addHandler(ui_handler)

    return logger


def register_ui_log_callback(callback: Callable[[str], None]) -> None:
    """Mendaftarkan callback fungsi GUI untuk menerima log real-time."""
    if callback not in _ui_callbacks:
        _ui_callbacks.append(callback)


def get_logger() -> logging.Logger:
    """Mengambil instance logger global."""
    return logging.getLogger(LOGGER_NAME)
