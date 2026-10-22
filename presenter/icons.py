"""Small geometric icons painted to match the glass dock."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap

from presenter.theme import ACCENT, IVORY


def _pen(color: QColor, width: float = 1.6) -> QPen:
    return QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


def paint_icon(painter: QPainter, name: str, bounds: QRectF, color: QColor) -> None:
    painter.save()
    painter.translate(bounds.center())
    scale = min(bounds.width(), bounds.height()) / 28.0
    painter.scale(scale, scale)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    _draw(painter, name, color)
    painter.restore()


def _draw(painter: QPainter, name: str, color: QColor) -> None:
    painter.setPen(_pen(color))
    if name == "mark":
        painter.setPen(_pen(ACCENT, 1.7))
        painter.drawEllipse(QPointF(0, 0), 7.2, 7.2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ACCENT)
        painter.drawEllipse(QPointF(0, 0), 2.1, 2.1)
        return
    if name == "spotlight":
        painter.drawEllipse(QPointF(0, 0), 7.1, 7.1)
        painter.drawEllipse(QPointF(0, 0), 3.15, 3.15)
        return
    if name == "laser":
        red = QColor(255, 48, 48)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(red)
        painter.drawEllipse(QPointF(0, 0), 2.35, 2.35)
        painter.setPen(_pen(red, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for angle in range(0, 360, 45):
            painter.save()
            painter.rotate(angle)
            painter.drawLine(QPointF(4.1, 0), QPointF(7.3, 0))
            painter.restore()
        return
    if name == "zoom":
        painter.drawEllipse(QPointF(-1.6, -1.6), 5.2, 5.2)
        painter.drawLine(QPointF(2.2, 2.2), QPointF(7.4, 7.4))
        return
    if name == "lens":
        painter.drawRoundedRect(QRectF(-7.4, -5.4, 14.8, 10.8), 2.6, 2.6)
        painter.drawEllipse(QPointF(0, 0), 3.3, 3.3)
        return
    if name == "draw":
        painter.drawLine(QPointF(-6.2, 6.4), QPointF(4.6, -4.4))
        painter.drawLine(QPointF(4.0, -3.6), QPointF(7.2, -6.8))
        painter.drawLine(QPointF(3.2, -6.2), QPointF(6.4, -3.0))
        return
    if name == "text":
        painter.drawLine(QPointF(-5.4, -6.0), QPointF(5.4, -6.0))
        painter.drawLine(QPointF(0, -6.0), QPointF(0, 6.6))
        return
    if name == "pen":
        painter.drawLine(QPointF(-5.5, 6.5), QPointF(5.2, -4.2))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(6.2, -5.4), 1.35, 1.35)
        return
    if name == "marker":
        marker = _pen(color, 4.8)
        marker.setCapStyle(Qt.PenCapStyle.SquareCap)
        painter.setPen(marker)
        painter.drawLine(QPointF(-5.6, 4.6), QPointF(3.6, -4.6))
        return
    if name == "line":
        painter.drawLine(QPointF(-6.5, 6.5), QPointF(6.5, -6.5))
        return
    if name == "arrow":
        _arrow(painter, QPointF(-6.5, 6.2), QPointF(6.6, -6.4), color, 1.6)
        return
    if name == "rect":
        painter.drawRoundedRect(QRectF(-6.2, -5.0, 12.4, 10.0), 2.0, 2.0)
        return
    if name == "ellipse":
        painter.drawEllipse(QRectF(-7.0, -5.0, 14.0, 10.0))
        return
    if name == "eraser":
        painter.drawRoundedRect(QRectF(-6.4, -4.6, 12.8, 9.2), 2.2, 2.2)
        painter.drawLine(QPointF(-3.0, -2.4), QPointF(3.2, 2.6))
        return
    if name == "frame":
        pen = _pen(color, 1.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRoundedRect(QRectF(-6.4, -5.0, 12.8, 10.0), 2.2, 2.2)
        return
    if name == "undo":
        painter.drawArc(QRectF(-5.5, -5.5, 11.0, 11.0), 40 * 16, 250 * 16)
        _arrow(painter, QPointF(-5.2, -1.5), QPointF(-7.4, 2.4), color, 1.6)
        return
    if name == "clear":
        painter.drawLine(QPointF(-4.2, -4.2), QPointF(4.2, 4.2))
        painter.drawLine(QPointF(-4.2, 4.2), QPointF(4.2, -4.2))
        return
    if name == "minus":
        painter.drawLine(QPointF(-5.5, 0), QPointF(5.5, 0))
        return
    if name == "plus":
        painter.drawLine(QPointF(-5.5, 0), QPointF(5.5, 0))
        painter.drawLine(QPointF(0, -5.5), QPointF(0, 5.5))
        return
    if name == "hide":
        painter.drawLine(QPointF(-5.5, -2.0), QPointF(0, 3.4))
        painter.drawLine(QPointF(0, 3.4), QPointF(5.5, -2.0))
        return
    if name == "help":
        painter.drawEllipse(QPointF(0, 0), 7.0, 7.0)
        painter.drawLine(QPointF(0, 1.2), QPointF(0, 3.4))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(0, -2.6), 1.15, 1.15)
        return
    if name == "pan":
        for angle in (0, 90, 180, 270):
            painter.save()
            painter.rotate(angle)
            painter.drawLine(QPointF(1.5, 0), QPointF(6.4, 0))
            painter.drawLine(QPointF(6.4, 0), QPointF(3.8, -2.1))
            painter.drawLine(QPointF(6.4, 0), QPointF(3.8, 2.1))
            painter.restore()
        return


def _arrow(painter: QPainter, start: QPointF, end: QPointF, color: QColor, width: float) -> None:
    angle = math.atan2(end.y() - start.y(), end.x() - start.x())
    head = 4.8
    painter.setPen(_pen(color, width))
    painter.drawLine(start, end)
    painter.drawLine(
        end,
        QPointF(end.x() - head * math.cos(angle - 0.45), end.y() - head * math.sin(angle - 0.45)),
    )
    painter.drawLine(
        end,
        QPointF(end.x() - head * math.cos(angle + 0.45), end.y() - head * math.sin(angle + 0.45)),
    )


def tray_pixmap(dpr: float = 2.0) -> QPixmap:
    side = 18
    pixmap = QPixmap(int(side * dpr), int(side * dpr))
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    paint_icon(painter, "mark", QRectF(0, 0, side, side), IVORY)
    painter.end()
    return pixmap
