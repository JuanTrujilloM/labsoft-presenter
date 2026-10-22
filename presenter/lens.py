"""Live magnifying glass that follows the pointer."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication

from presenter.capture import capture_region
from presenter.cocoa import FloatingWindow
from presenter.theme import ACCENT, DOCK_SHADOW, GLASS, format_mag, ui_font


class Lens(FloatingWindow):
    level_offset = 1

    def __init__(self) -> None:
        super().__init__()
        self.set_click_through(True)
        self._pixmap = QPixmap()
        self._power = 2.5
        self._failed = False
        self.image = QRect(0, 0, 380, 232)
        left, top, right, bottom = DOCK_SHADOW
        self.setFixedSize(self.image.width() + left + right, self.image.height() + top + bottom)
        self.hide()

    def refresh(self, power: float, below_window: int | None) -> None:
        self._power = power
        cursor = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor) or QApplication.primaryScreen()
        if screen is None:
            return
        self._move_near(cursor, screen)
        captured = capture_region(self._capture_rect(cursor, screen, power), below_window)
        self._failed = captured.isNull()
        self._pixmap = captured
        if not self.isVisible():
            self.show()
        self.update()

    def _move_near(self, cursor: QPoint, screen) -> None:
        avail = screen.availableGeometry()
        gap = 26
        x = cursor.x() - self.width() // 2
        y = cursor.y() - self.height() - gap
        if y < avail.top() + 8:
            y = cursor.y() + gap
        x = max(avail.left() + 8, min(x, avail.right() - self.width() - 8))
        y = max(avail.top() + 8, min(y, avail.bottom() - self.height() - 8))
        self.move(int(x), int(y))

    def _capture_rect(self, cursor: QPoint, screen, power: float) -> QRect:
        power = max(power, 1.2)
        width = max(24, int(self.image.width() / power))
        height = max(24, int(self.image.height() / power))
        rect = QRect(int(cursor.x() - width / 2), int(cursor.y() - height / 2), width, height)
        return rect.intersected(screen.geometry())

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        left, top, right, bottom = DOCK_SHADOW
        plate = QRectF(self.rect()).adjusted(left, top, -right, -bottom)
        painter.setPen(Qt.PenStyle.NoPen)
        for index, alpha in enumerate((12, 18, 26)):
            shadow = plate.adjusted(-1, 5 + index, 1, 8 + index)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(shadow, 20, 20)
        painter.setBrush(GLASS)
        painter.drawRoundedRect(plate, 18, 18)
        image_rect = plate.adjusted(6, 6, -6, -6)
        painter.setClipPath(_rounded(image_rect, 14))
        if self._failed or self._pixmap.isNull():
            painter.fillRect(image_rect, QColor(12, 12, 14))
            painter.setClipping(False)
            painter.setPen(QColor(247, 244, 236, 180))
            painter.setFont(ui_font(12))
            painter.drawText(image_rect, int(Qt.AlignmentFlag.AlignCenter), "Permite Grabación de pantalla\npara usar la lupa")
        else:
            painter.drawPixmap(image_rect, self._pixmap, QRectF(self._pixmap.rect()))
            painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 255, 255, 46), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(image_rect, 14, 14)
        self._paint_power(painter, image_rect)
        painter.end()

    def _paint_power(self, painter: QPainter, image_rect: QRectF) -> None:
        label = format_mag(self._power)
        painter.setFont(ui_font(11, QFont.Weight.Medium))
        text_width = painter.fontMetrics().horizontalAdvance(label) + 16
        chip = QRectF(image_rect.right() - text_width - 10, image_rect.top() + 10, text_width, 22)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(16, 16, 18, 170))
        painter.drawRoundedRect(chip, 8, 8)
        painter.setPen(ACCENT)
        painter.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), label)


def _rounded(rect: QRectF, radius: float):
    from PyQt6.QtGui import QPainterPath

    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path
