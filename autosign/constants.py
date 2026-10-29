"""Konstanta aplikasi, styling tema, dan path default."""

from enum import Enum
import customtkinter as ctk

# Inisialisasi default CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Theme Colors (ArcGIS Pro Style)
ARC_BLUE = "#007ac2"
ARC_BLUE_HOVER = "#005e95"
BG_PANEL = ("#dbdbdb", "#2b2b2b")

# Action Colors
COLOR_SUCCESS = "#27ae60"
COLOR_DANGER = "#c0392b"
COLOR_DANGER_HOVER = "#a93226"
COLOR_WARNING = "#f39c12"
COLOR_ORANGE = "#d35400"
COLOR_ACCENT = "#8e44ad"
COLOR_SECONDARY = "#34495e"
COLOR_INFO = "#2980b9"
COLOR_LOG_TEXT = "#00ff00"
COLOR_LOG_BG = "#121212"

# Paths
PROFILES_DIR_NAME = "profiles"
SETTINGS_FILE_NAME = "settings.json"

# UI Defaults
DEFAULT_BUTTON_STYLE = {
    "corner_radius": 6,
    "height": 35,
    "font": ("Arial", 12, "bold")
}


class DragMode(Enum):
    """Mode interaksi kursor pada layout designer canvas."""
    NONE = 0
    MOVE = 1
    RESIZE = 2
