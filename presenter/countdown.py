"""A countdown that stays on one screen."""

from __future__ import annotations

import math
import time

from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen

from presenter.cocoa import FloatingWindow
from presenter.theme import ACCENT, DOCK_RADIUS, DOCK_SHADOW, GLASS, IVORY, ui_font


def format_clock(seconds: int) -> str:
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


class Countdown(FloatingWindow):
    """Large remaining time, pinned to the screen that was chosen."""

    level_offset = 1

    def __init__(self) -> None:
        super().__init__()
        self.set_click_through(True)
        self.setFixedSize(292, 148)
        self._remaining = 0
        self._deadline = 0.0
        self._done = False
        self._pulse = QTimer(self)
        self._pulse.setInterval(100)
        self._pulse.timeout.connect(self._tick)
        self.hide()

    def start(self, screen, seconds: int) -> None:
        self._done = False
        self._remaining = max(0, seconds)
        self._deadline = time.monotonic() + self._remaining
        self._place(screen)
        self._pulse.start()
        self.show()
        self.apply_native()
        self.raise_()
        self.update()

    def stop(self) -> None:
        self._pulse.stop()
        self._done = False
        self.hide()

    def _tick(self) -> None:
        left = self._deadline - time.monotonic()
        if left <= 0:
            self._remaining = 0
            self._done = True
            self._pulse.stop()
        else:
            self._remaining = math.ceil(left)
        self.update()

    def _place(self, screen) -> None:
        geo = screen.geometry()
        self.winId()
        handle = self.windowHandle()
        if handle is not None and handle.screen() is not screen:
            handle.setScreen(screen)
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + max(48, int(geo.height() * 0.12))
        self.setGeometry(x, y, self.width(), self.height())

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        left, top, right, bottom = DOCK_SHADOW
        glass = QRectF(self.rect()).adjusted(left, top, -right, -bottom)
        painter.setPen(Qt.PenStyle.NoPen)
        for index, alpha in enumerate((12, 18, 24, 30)):
            shadow = glass.adjusted(-0.4, 4 + index * 0.8, 0.4, 6 + index)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(shadow, DOCK_RADIUS + 1, DOCK_RADIUS + 1)
        painter.setPen(QPen(QColor(255, 255, 255, 38), 1))
        painter.setBrush(GLASS)
        painter.drawRoundedRect(glass, DOCK_RADIUS, DOCK_RADIUS)
        painter.setFont(ui_font(52, QFont.Weight.DemiBold))
        painter.setPen(QColor(255, 92, 86) if self._done else (ACCENT if self._remaining <= 10 and self._remaining > 0 else IVORY))
        painter.drawText(glass, int(Qt.AlignmentFlag.AlignCenter), format_clock(self._remaining))
        painter.end()
