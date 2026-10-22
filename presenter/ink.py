"""Painting strokes, words, and element frames."""

from __future__ import annotations

import math

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen

from presenter.model import Note, Stroke, visual_width
from presenter.theme import ACCENT, ui_font


def smooth_path(points: list[QPointF]) -> QPainterPath:
    path = QPainterPath(points[0])
    if len(points) == 2:
        path.lineTo(points[1])
        return path
    for index in range(1, len(points) - 1):
        current = points[index]
        nxt = points[index + 1]
        midpoint = QPointF((current.x() + nxt.x()) / 2, (current.y() + nxt.y()) / 2)
        path.quadTo(current, midpoint)
    path.lineTo(points[-1])
    return path


def paint_arrow(painter: QPainter, start: QPointF, end: QPointF, color: QColor, width: float) -> None:
    angle = math.atan2(end.y() - start.y(), end.x() - start.x())
    length = math.hypot(end.x() - start.x(), end.y() - start.y())
    if length < 1:
        return
    head = min(length * 0.45, 8 + width * 2.1)
    tip_inset = head * 0.55
    line_end = QPointF(end.x() - math.cos(angle) * tip_inset, end.y() - math.sin(angle) * tip_inset)
    painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawLine(QLineF(start, line_end))
    left = QPointF(end.x() - head * math.cos(angle - 0.42), end.y() - head * math.sin(angle - 0.42))
    right = QPointF(end.x() - head * math.cos(angle + 0.42), end.y() - head * math.sin(angle + 0.42))
    path = QPainterPath(left)
    path.lineTo(end)
    path.lineTo(right)
    path.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPath(path)


def paint_stroke(painter: QPainter, stroke: Stroke, points: list[QPointF], scale: float) -> None:
    if not points:
        return
    color = QColor(stroke.color)
    width = visual_width(stroke.kind, stroke.width) * scale
    if stroke.kind == "marker":
        color.setAlpha(78)
    pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if stroke.kind in ("pen", "marker"):
        if len(points) == 1:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(points[0], width / 2, width / 2)
            return
        painter.drawPath(smooth_path(points))
        return
    if len(points) < 2:
        return
    start, end = points[0], points[-1]
    rect = QRectF(start, end).normalized()
    if stroke.kind == "line":
        painter.drawLine(QLineF(start, end))
    elif stroke.kind == "arrow":
        paint_arrow(painter, start, end, color, max(width, 1.4))
    elif stroke.kind == "rect":
        radius = min(10.0 * scale, rect.width() / 3, rect.height() / 3)
        painter.drawRoundedRect(rect, radius, radius)
    elif stroke.kind == "ellipse":
        painter.drawEllipse(rect)


def note_font(size: int) -> QFont:
    font = ui_font(max(size, 8), QFont.Weight.Medium)
    return font


def measure_note(text: str, size: int) -> QRectF:
    metrics = QFontMetrics(note_font(size))
    bounds = metrics.boundingRect(0, 0, 720, 800, int(Qt.TextFlag.TextDontClip), text)
    return QRectF(0, 0, max(8, bounds.width() + 2), max(metrics.height(), bounds.height() + 2))


def paint_note(painter: QPainter, note: Note, origin: QPointF, scale: float) -> None:
    size = max(8, int(round(note.size * scale)))
    font = note_font(size)
    painter.setFont(font)
    bounds = measure_note(note.text, size)
    rect = QRectF(origin.x(), origin.y(), bounds.width(), bounds.height())
    painter.setPen(QColor(0, 0, 0, 130))
    painter.drawText(
        rect.translated(0, 1.2 * scale),
        int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextDontClip),
        note.text,
    )
    painter.setPen(note.color)
    painter.drawText(
        rect,
        int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextDontClip),
        note.text,
    )


def paint_frame(painter: QPainter, rect: QRectF, scale: float) -> None:
    if rect.width() < 2 or rect.height() < 2:
        return
    radius = min(12.0 * scale, rect.width() / 3, rect.height() / 3)
    glow = QColor(ACCENT)
    for width, alpha in ((10 * scale, 22), (6 * scale, 36), (3.2 * scale, 54)):
        glow.setAlpha(alpha)
        painter.setPen(QPen(glow, max(1.0, width), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
    painter.setPen(QPen(ACCENT, max(1.4, 1.7 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawRoundedRect(rect, radius, radius)
    inset = rect.adjusted(2.2 * scale, 2.2 * scale, -2.2 * scale, -2.2 * scale)
    if inset.width() > 4 and inset.height() > 4:
        inner = QColor(255, 255, 255, 70)
        painter.setPen(QPen(inner, max(1.0, 1.0 * scale)))
        painter.drawRoundedRect(inset, max(1.0, radius - 2), max(1.0, radius - 2))
