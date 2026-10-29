"""Komponen helper tooltip ringan berbasis Tkinter bawaan tanpa pustaka eksternal."""

import tkinter as tk
from typing import Optional


class ToolTip:
    """Menampilkan tooltip informatif saat mouse diarahkan ke widget."""

    def __init__(self, widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tip_window: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event=None) -> None:
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _on_leave(self, _event=None) -> None:
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

    def _show(self) -> None:
        if self.tip_window or not self.text:
            return

        try:
            # Koordinat widget di layar
            x = self.widget.winfo_rootx() + (self.widget.winfo_width() // 2)
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes("-topmost", True)

            label = tk.Label(
                tw,
                text=self.text,
                justify="left",
                background="#1e1e1e",
                foreground="#f0f0f0",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 9),
                padx=8,
                pady=4
            )
            label.pack()
        except Exception:
            pass
