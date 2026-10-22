"""Painted controls for the floating tool bar."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QAbstractButton, QWidget

from presenter.icons import paint_icon
from presenter.theme import ACCENT, IVORY, ui_font


class IconButton(QAbstractButton):
    def __init__(self, name: str, tip: str, *, checkable: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._name = name
        self.setToolTip(tip)
        self.setCheckable(checkable)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        color = QColor(IVORY)
        if not self.isEnabled():
            color.setAlpha(70)
        elif self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(231, 177, 90, 46))
            painter.drawRoundedRect(rect, 12, 12)
            color = QColor(ACCENT)
        elif self.underMouse():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 18))
            painter.drawRoundedRect(rect, 12, 12)
        paint_icon(painter, self._name, QRectF(self.rect()), color)
        painter.end()


class TextButton(QAbstractButton):
    def __init__(self, label: str, *, gold: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._label = label
        self._gold = gold
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(ui_font(12, QFont.Weight.Medium))
        self.setFixedHeight(32)
        width = self.fontMetrics().horizontalAdvance(label) + 22
        self.setFixedWidth(max(width, 52))

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._gold:
            painter.setBrush(QColor(231, 177, 90, 56 if self.underMouse() else 32))
        elif self.isChecked():
            painter.setBrush(QColor(231, 177, 90, 42))
        elif self.underMouse():
            painter.setBrush(QColor(255, 255, 255, 20))
        else:
            painter.setBrush(QColor(255, 255, 255, 12))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 10, 10)
        if self.isChecked() or self._gold:
            painter.setPen(ACCENT)
        else:
            painter.setPen(QColor(247, 244, 236, 225))
        painter.setFont(self.font())
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._label)
        painter.end()


class ColorDot(QAbstractButton):
    def __init__(self, hex_color: str, parent=None) -> None:
        super().__init__(parent)
        self.hex_color = hex_color
        self._color = QColor(hex_color)
        self.setCheckable(True)
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(hex_color)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isChecked():
            painter.setPen(QPen(IVORY, 1.7))
        else:
            painter.setPen(QPen(QColor(255, 255, 255, 46), 1))
        painter.setBrush(self._color)
        painter.drawEllipse(QRectF(self.rect()).adjusted(3.2, 3.2, -3.2, -3.2))
        painter.end()


class ThinSlider(QWidget):
    changed = pyqtSignal(float)

    def __init__(self, low: float, high: float, value: float, parent=None) -> None:
        super().__init__(parent)
        self._low = low
        self._high = high
        self._value = value
        self.setFixedSize(118, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_value(self, value: float) -> None:
        self._value = min(self._high, max(self._low, value))
        self.update()

    def _ratio(self) -> float:
        span = self._high - self._low
        if span <= 0:
            return 0.0
        return (self._value - self._low) / span

    def _x(self) -> float:
        return 8 + self._ratio() * (self.width() - 16)

    def _apply_x(self, x: float) -> None:
        ratio = (x - 8) / max(1.0, self.width() - 16)
        ratio = min(1.0, max(0.0, ratio))
        value = self._low + ratio * (self._high - self._low)
        if abs(value - self._value) < 1e-4:
            return
        self._value = value
        self.changed.emit(value)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._apply_x(event.position().x())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._apply_x(event.position().x())

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() / 2
        track = QPen(QColor(255, 255, 255, 32), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track)
        painter.drawLine(QPointF(8, y), QPointF(self.width() - 8, y))
        painter.setPen(QPen(ACCENT, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(8, y), QPointF(self._x(), y))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(IVORY)
        painter.drawEllipse(QPointF(self._x(), y), 5.5, 5.5)
        painter.setBrush(ACCENT)
        painter.drawEllipse(QPointF(self._x(), y), 3.1, 3.1)
        painter.end()


class Hairline(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(10, 22)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(4, 2, 1, self.height() - 4, QColor(255, 255, 255, 32))
        painter.end()
