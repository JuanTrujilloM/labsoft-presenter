"""Ink, highlights, and undo for a presentation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor


def dist(a: QPointF, b: QPointF) -> float:
    return math.hypot(a.x() - b.x(), a.y() - b.y())


def dist_segment(point: QPointF, start: QPointF, end: QPointF) -> float:
    dx = end.x() - start.x()
    dy = end.y() - start.y()
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-6:
        return dist(point, start)
    t = max(0.0, min(1.0, ((point.x() - start.x()) * dx + (point.y() - start.y()) * dy) / length_sq))
    projection = QPointF(start.x() + t * dx, start.y() + t * dy)
    return dist(point, projection)


def visual_width(kind: str, width: float) -> float:
    if kind == "marker":
        return max(width * 4.4, 20.0)
    return width


@dataclass
class Stroke:
    kind: str
    color: QColor
    width: float
    points: list[QPointF]


@dataclass
class Note:
    origin: QPointF
    text: str
    color: QColor
    size: int
    bounds: QRectF


@dataclass
class Frame:
    rect: QRectF


@dataclass(frozen=True)
class UiState:
    mode: str = "idle"
    shape: str = "pen"
    inking: bool = False
    framing: bool = False
    zoom: float = 2.0
    lens_power: float = 2.5
    dim: float = 0.62
    radius: float = 180.0
    width: float = 3.5
    text_size: int = 36
    color: str = "#FF4D3A"
    can_undo: bool = False
    hint: str = ""
    message: str = ""


def hits_stroke(stroke: Stroke, point: QPointF, radius: float) -> bool:
    if not stroke.points:
        return False
    threshold = radius + visual_width(stroke.kind, stroke.width) * 0.5
    kind = stroke.kind
    if kind in ("pen", "marker"):
        if len(stroke.points) == 1:
            return dist(point, stroke.points[0]) <= threshold
        return any(
            dist_segment(point, stroke.points[i], stroke.points[i + 1]) <= threshold
            for i in range(len(stroke.points) - 1)
        )
    if len(stroke.points) < 2:
        return False
    start, end = stroke.points[0], stroke.points[-1]
    rect = QRectF(start, end).normalized()
    if kind in ("line", "arrow"):
        return dist_segment(point, start, end) <= threshold
    if kind == "rect":
        outer = rect.adjusted(-threshold, -threshold, threshold, threshold)
        inner = rect.adjusted(threshold, threshold, -threshold, -threshold)
        if not outer.contains(point):
            return False
        if inner.width() <= 0 or inner.height() <= 0:
            return True
        return not inner.contains(point)
    if kind == "ellipse":
        if rect.width() < 1 or rect.height() < 1:
            return dist(point, rect.center()) <= threshold
        rx = max(rect.width() / 2, 0.5)
        ry = max(rect.height() / 2, 0.5)
        nx = (point.x() - rect.center().x()) / rx
        ny = (point.y() - rect.center().y()) / ry
        tolerance = threshold / max(min(rx, ry), 1.0)
        return abs(math.hypot(nx, ny) - 1.0) <= tolerance
    return False


class Document:
    """Screen-space annotations. Coordinates are global logical pixels."""

    def __init__(self) -> None:
        self.strokes: list[Stroke] = []
        self.notes: list[Note] = []
        self.frames: list[Frame] = []
        self._undo: list[tuple] = []
        self._batch: list[tuple[list[Stroke], list[Note], list[Frame]]] | None = None

    @property
    def has_ink(self) -> bool:
        return bool(self.strokes or self.notes or self.frames)

    def can_undo(self) -> bool:
        return bool(self._undo)

    def add_stroke(self, stroke: Stroke) -> None:
        self.strokes.append(stroke)
        self._push(("stroke", stroke))

    def add_note(self, note: Note) -> None:
        self.notes.append(note)
        self._push(("note", note))

    def add_frame(self, frame: Frame) -> None:
        self.frames.append(frame)
        self._push(("frame", frame))

    def begin_erase(self) -> None:
        self._batch = []

    def erase_at(self, point: QPointF, radius: float) -> bool:
        removed_strokes = [stroke for stroke in self.strokes if hits_stroke(stroke, point, radius)]
        removed_notes = [
            note
            for note in self.notes
            if note.bounds.adjusted(-radius, -radius, radius, radius).contains(point)
        ]
        removed_frames = [
            frame
            for frame in self.frames
            if frame.rect.adjusted(-radius, -radius, radius, radius).contains(point)
        ]
        if not removed_strokes and not removed_notes and not removed_frames:
            return False
        stroke_ids = {id(stroke) for stroke in removed_strokes}
        note_ids = {id(note) for note in removed_notes}
        frame_ids = {id(frame) for frame in removed_frames}
        self.strokes = [stroke for stroke in self.strokes if id(stroke) not in stroke_ids]
        self.notes = [note for note in self.notes if id(note) not in note_ids]
        self.frames = [frame for frame in self.frames if id(frame) not in frame_ids]
        change = (removed_strokes, removed_notes, removed_frames)
        if self._batch is not None:
            self._batch.append(change)
        else:
            self._push(("restore", change))
        return True

    def end_erase(self) -> None:
        if self._batch:
            strokes: list[Stroke] = []
            notes: list[Note] = []
            frames: list[Frame] = []
            for removed_strokes, removed_notes, removed_frames in self._batch:
                strokes.extend(removed_strokes)
                notes.extend(removed_notes)
                frames.extend(removed_frames)
            if strokes or notes or frames:
                self._push(("restore", (strokes, notes, frames)))
        self._batch = None

    def clear(self) -> None:
        if not self.has_ink:
            return
        self._push(("clear", (list(self.strokes), list(self.notes), list(self.frames))))
        self.strokes = []
        self.notes = []
        self.frames = []

    def undo(self) -> None:
        if not self._undo:
            return
        kind, payload = self._undo.pop()
        if kind == "stroke":
            self.strokes = [item for item in self.strokes if item is not payload]
        elif kind == "note":
            self.notes = [item for item in self.notes if item is not payload]
        elif kind == "frame":
            self.frames = [item for item in self.frames if item is not payload]
        elif kind == "restore":
            strokes, notes, frames = payload
            self.strokes.extend(strokes)
            self.notes.extend(notes)
            self.frames.extend(frames)
        elif kind == "clear":
            strokes, notes, frames = payload
            self.strokes = list(strokes)
            self.notes = list(notes)
            self.frames = list(frames)

    def _push(self, item: tuple) -> None:
        self._undo.append(item)
        if len(self._undo) > 100:
            del self._undo[:-100]
