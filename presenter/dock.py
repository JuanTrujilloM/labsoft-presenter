"""The glass tool bar and the shortcut guide."""

from __future__ import annotations

import random
from pathlib import Path

from PyQt6.QtCore import QPoint, QRectF, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from presenter.capture import screen_recording_allowed
from presenter.cocoa import (
    FloatingWindow,
    accessibility_trusted,
    request_accessibility,
    request_screen_recording,
    set_native_level,
)
from presenter.icons import paint_icon
from presenter.model import UiState
from presenter.theme import ACCENT, DOCK_PAD, DOCK_RADIUS, DOCK_SHADOW, GLASS, IVORY, PALETTE, format_mag, ui_font
from presenter.widgets import ColorDot, Hairline, IconButton, TextButton, ThinSlider

_SHAPES = ("pen", "marker", "line", "arrow", "rect", "ellipse")


def names_from_text(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def spin_sequence(names: list[str], winner: str, length: int = 15) -> list[str]:
    """Teaser names, then the chosen one. The winner stays off the reel until the end."""
    teasers = 4 if len(names) < 2 else max(length - 1, 1)
    frames: list[str] = []
    previous = None
    for _ in range(teasers):
        options = [name for name in names if name != previous and name != winner]
        if not options:
            options = [name for name in names if name != previous] or list(names)
        previous = random.choice(options)
        frames.append(previous)
    frames.append(winner)
    return frames


def _spin_delay(index: int, total: int) -> int:
    span = max(total - 1, 1)
    progress = index / span
    return int(32 + (progress * progress) * 170)


def _screen_label(screen) -> str:
    name = (screen.name() or "").strip()
    folded = name.lower()
    if "built-in" in folded or "integrad" in folded:
        return "Integrada"
    if not name:
        return "Pantalla"
    return name if len(name) <= 18 else name[:17] + "…"


def _transparent(widget: QWidget) -> QWidget:
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    widget.setAutoFillBackground(False)
    widget.setStyleSheet("background: transparent;")
    return widget


class Mark(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(34, 36)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._offset: QPoint | None = None

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_icon(painter, "mark", QRectF(self.rect()), ACCENT)
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._offset = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._offset)

    def mouseReleaseEvent(self, _event) -> None:  # noqa: N802
        self._offset = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)


class _Glass(FloatingWindow):
    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
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
        painter.end()


class Guide(_Glass):
    level_offset = 4

    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(468)
        root = QVBoxLayout(self)
        left, top, right, bottom = DOCK_SHADOW
        root.setContentsMargins(left + 18, top + 16, right + 18, bottom + 16)
        root.setSpacing(8)

        title = QLabel("Presenter")
        title.setFont(ui_font(20, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #F7F4EC; background: transparent;")
        subtitle = QLabel("Resalta un elemento, amplíalo, escribe o elige un estudiante al azar.")
        subtitle.setFont(ui_font(12))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: rgba(247,244,236,0.62); background: transparent;")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(4)

        rows = (
            ("Resaltar", "⌃⌥H", "Oscurece la sala y enmarca un elemento"),
            ("Láser", "⌃⌥L", "La luz es el puntero"),
            ("Zoom", "⌃⌥Z", "Elige la pantalla y amplía solo ahí"),
            ("Dibujar", "⌃⌥D", "Pluma, marcador, flechas y formas"),
            ("Escribir", "⌃⌥T", "Escribe sobre la diapositiva"),
            ("Azar", "dado", "Carga nombres, elige uno y quita quien no está"),
            ("Herramientas", "⌃⌥P", "Muestra u oculta esta barra"),
            ("Volver", "Esc", "Un paso atrás. La tinta se queda"),
            ("Deshacer", "⌘Z", "Quita la última marca"),
        )
        for name, keys, detail in rows:
            root.addWidget(self._row(name, keys, detail))

        root.addSpacing(6)
        self.access_label = self._note("")
        self.screen_label = self._note("")
        root.addWidget(self.access_label)
        root.addWidget(self.screen_label)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.allow_access = TextButton("Permitir atajos")
        self.allow_screen = TextButton("Permitir captura")
        close = TextButton("Cerrar", gold=True)
        self.allow_access.clicked.connect(request_accessibility)
        self.allow_screen.clicked.connect(request_screen_recording)
        close.clicked.connect(self.hide)
        actions.addWidget(self.allow_access)
        actions.addWidget(self.allow_screen)
        actions.addWidget(close)
        root.addLayout(actions)
        self.hide()

    def present_over(self, dock: QWidget) -> None:
        self.refresh_status()
        self.adjustSize()
        anchor = dock.frameGeometry()
        screen = QGuiApplication.screenAt(anchor.center()) or QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen is not None else anchor
        x = anchor.center().x() - self.width() // 2
        y = anchor.top() - self.height() - 10
        if y < avail.top() + 8:
            y = anchor.bottom() + 10
        x = max(avail.left() + 8, min(x, avail.right() - self.width() - 8))
        y = max(avail.top() + 8, min(y, avail.bottom() - self.height() - 8))
        self.move(int(x), int(y))
        self.show()
        self.raise_()

    def refresh_status(self) -> None:
        if accessibility_trusted():
            self.access_label.setText("Los atajos están listos.")
            self.allow_access.hide()
        else:
            self.access_label.setText("Activa Accesibilidad para esta app y poder usar los atajos.")
            self.allow_access.show()
        if screen_recording_allowed():
            self.screen_label.setText("La captura de pantalla está lista para el zoom.")
            self.allow_screen.hide()
        else:
            self.screen_label.setText("Permite Grabación de pantalla, cierra Presenter y ábrelo de nuevo.")
            self.allow_screen.show()

    @staticmethod
    def _note(text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(ui_font(11))
        label.setStyleSheet("color: rgba(231,177,90,0.9); background: transparent;")
        return label

    @staticmethod
    def _row(name: str, keys: str, detail: str) -> QWidget:
        row = _transparent(QWidget())
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(8)
        title = QLabel(name)
        title.setFont(ui_font(13, QFont.Weight.Medium))
        title.setStyleSheet("color: #F7F4EC; background: transparent;")
        title.setFixedWidth(124)
        badge = QLabel(keys)
        badge.setFont(ui_font(11, QFont.Weight.Medium))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(62)
        badge.setFixedHeight(22)
        badge.setStyleSheet(
            "color: #E7B15A; background-color: rgba(231, 177, 90, 0.14); border-radius: 6px;"
        )
        body = QLabel(detail)
        body.setFont(ui_font(12))
        body.setStyleSheet("color: rgba(247,244,236,0.66); background: transparent;")
        layout.addWidget(title)
        layout.addWidget(badge)
        layout.addWidget(body, 1)
        return row


class Dock(_Glass):
    action = pyqtSignal(str)
    colorPicked = pyqtSignal(QColor)
    widthChanged = pyqtSignal(float)
    dimChanged = pyqtSignal(float)

    level_offset = 3

    def __init__(self) -> None:
        super().__init__()
        self._state: UiState | None = None
        self._collapsed = False
        self._ready = False
        self._zoom_screens: tuple = ()
        self._roster_open = False
        self._names: list[str] = []
        self._pool: list[str] = []
        self._picked = ""
        self._roster_error = ""
        self._flags_before_dialog = None
        self._spinning = False
        self._spin_frames: list[str] = []
        self._spin_index = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.setSingleShot(True)
        self._spin_timer.timeout.connect(self._spin_tick)

        self.mark = Mark()
        self.laser = IconButton("laser", checkable=True)
        self.spotlight = IconButton("spotlight", checkable=True)
        self.zoom = IconButton("zoom", checkable=True)
        self.draw = IconButton("draw", checkable=True)
        self.text = IconButton("text", checkable=True)
        self.random_btn = IconButton("random", checkable=True)
        self.help = IconButton("help")
        self.hide_btn = IconButton("hide")
        self.quit_btn = TextButton("Salir")

        self.minus = IconButton("minus")
        self.plus = IconButton("plus")
        self.metric = QLabel("2×")
        self.metric.setFont(ui_font(12, QFont.Weight.Medium))
        self.metric.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.metric.setFixedWidth(58)
        self.metric.setStyleSheet("color: #F7F4EC; background: transparent;")

        self.pan = TextButton("Mover")
        self.pan.setCheckable(True)
        self.frame = TextButton("Marco")
        self.frame.setCheckable(True)
        self.shapes = {
            name: IconButton(name, checkable=True) for name in _SHAPES
        }
        self.ink_text = IconButton("text", checkable=True)

        self.dots = [ColorDot(color) for color in PALETTE]
        self.palette = _transparent(QWidget())
        palette_row = QHBoxLayout(self.palette)
        palette_row.setContentsMargins(0, 0, 0, 0)
        palette_row.setSpacing(1)
        for dot in self.dots:
            palette_row.addWidget(dot)
            dot.clicked.connect(lambda _checked=False, color=dot.hex_color: self.colorPicked.emit(QColor(color)))

        self.width_slider = ThinSlider(1.2, 16.0, 3.5)
        self.dim_slider = ThinSlider(0.22, 0.84, 0.62)
        self.shade = QLabel("Sombra")
        self.shade.setFont(ui_font(11))
        self.shade.setStyleSheet("color: rgba(247,244,236,0.55); background: transparent;")
        self.undo = IconButton("undo")
        self.clear_btn = TextButton("Borrar")
        self.done = TextButton("Listo", gold=True)
        self.hair_a = Hairline()
        self.hair_b = Hairline()
        self.hair_c = Hairline()

        self.hint = QLabel("Resalta, amplía y escribe sobre la diapositiva")
        self.hint.setFont(ui_font(11))
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setWordWrap(True)
        self.hint.setMaximumWidth(560)

        self.pill = _transparent(QWidget())
        pill_row = QHBoxLayout(self.pill)
        pill_row.setContentsMargins(2, 0, 2, 0)
        pill_row.setSpacing(4)
        self.pill_mark = Mark()
        self.pill_btn = TextButton("Presenter", gold=True)
        pill_row.addWidget(self.pill_mark)
        pill_row.addWidget(self.pill_btn)

        self.tools = _transparent(QWidget())
        tools = QHBoxLayout(self.tools)
        tools.setContentsMargins(0, 0, 0, 0)
        tools.setSpacing(2)
        tools.addWidget(self.mark)
        tools.addSpacing(4)
        for button in (self.laser, self.spotlight, self.zoom):
            tools.addWidget(button)
        tools.addSpacing(6)
        tools.addWidget(self.draw)
        tools.addWidget(self.text)
        tools.addSpacing(6)
        tools.addWidget(self.random_btn)
        tools.addSpacing(6)
        tools.addWidget(self.help)
        tools.addWidget(self.hide_btn)
        tools.addSpacing(6)
        tools.addWidget(self.quit_btn)

        self.screens_box = _transparent(QWidget())
        self._zoom_screen_row = QHBoxLayout(self.screens_box)
        self._zoom_screen_row.setContentsMargins(0, 0, 0, 0)
        self._zoom_screen_row.setSpacing(6)

        self.context = _transparent(QWidget())
        context = QHBoxLayout(self.context)
        context.setContentsMargins(0, 0, 0, 0)
        context.setSpacing(3)
        context.addStretch(1)
        context.addWidget(self.screens_box)
        self.screens_box.hide()
        context.addWidget(self.minus)
        context.addWidget(self.metric)
        context.addWidget(self.plus)
        context.addWidget(self.pan)
        context.addWidget(self.frame)
        for name in _SHAPES:
            context.addWidget(self.shapes[name])
        context.addWidget(self.ink_text)
        context.addWidget(self.hair_a)
        context.addWidget(self.palette)
        context.addWidget(self.hair_b)
        context.addWidget(self.shade)
        context.addWidget(self.dim_slider)
        context.addWidget(self.width_slider)
        context.addWidget(self.hair_c)
        context.addWidget(self.undo)
        context.addWidget(self.clear_btn)
        context.addWidget(self.done)
        context.addStretch(1)

        self.roster = _transparent(QWidget())
        roster_root = QVBoxLayout(self.roster)
        roster_root.setContentsMargins(0, 0, 0, 0)
        roster_root.setSpacing(4)
        roster_row = QHBoxLayout()
        roster_row.setContentsMargins(0, 0, 0, 0)
        roster_row.setSpacing(6)
        self.roster_load = TextButton("Cargar lista")
        self.roster_pick = TextButton("Elegir", gold=True)
        self.roster_status = QLabel("")
        self.roster_status.setFont(ui_font(12))
        self.roster_status.setStyleSheet("color: rgba(247,244,236,0.62); background: transparent;")
        roster_row.addStretch(1)
        roster_row.addWidget(self.roster_load)
        roster_row.addWidget(self.roster_pick)
        roster_row.addWidget(self.roster_status)
        roster_row.addStretch(1)
        self.roster_name = QLabel("")
        self.roster_name.setFont(ui_font(22, QFont.Weight.DemiBold))
        self.roster_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.roster_name.setWordWrap(True)
        self.roster_name.setMaximumWidth(480)
        self.roster_name.setMinimumWidth(320)
        self.roster_name.setMinimumHeight(52)
        self.roster_name.setStyleSheet("color: #E7B15A; background: transparent;")
        roster_root.addLayout(roster_row)
        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(8)
        self.roster_remove = IconButton("trash")
        name_row.addStretch(1)
        name_row.addWidget(self.roster_name)
        name_row.addWidget(self.roster_remove)
        name_row.addStretch(1)
        roster_root.addLayout(name_row)
        self.roster_pick.hide()
        self.roster_name.hide()
        self.roster_remove.hide()
        self.roster.hide()

        root = QVBoxLayout(self)
        left, top, right, bottom = DOCK_SHADOW
        root.setContentsMargins(left + DOCK_PAD, top + DOCK_PAD, right + DOCK_PAD, bottom + DOCK_PAD)
        root.setSpacing(6)
        root.addWidget(self.tools)
        root.addWidget(self.roster)
        root.addWidget(self.context)
        root.addWidget(self.hint)
        root.addWidget(self.pill)
        self.pill.hide()
        self.context.hide()

        self._wire()

    def _wire(self) -> None:
        self.laser.clicked.connect(lambda _=False: self.action.emit("laser"))
        self.spotlight.clicked.connect(lambda _=False: self.action.emit("spotlight"))
        self.zoom.clicked.connect(lambda _=False: self.action.emit("zoom"))
        self.draw.clicked.connect(lambda _=False: self.action.emit("draw"))
        self.text.clicked.connect(lambda _=False: self.action.emit("text"))
        self.random_btn.clicked.connect(self._toggle_roster)
        self.roster_load.clicked.connect(self._load_roster)
        self.roster_pick.clicked.connect(self._pick_student)
        self.roster_remove.clicked.connect(self._remove_picked)
        self.help.clicked.connect(lambda _=False: self.action.emit("help"))
        self.hide_btn.clicked.connect(lambda _=False: self.action.emit("hide"))
        self.quit_btn.clicked.connect(lambda _=False: self.action.emit("quit"))
        self.minus.clicked.connect(lambda _=False: self.action.emit("nudge-down"))
        self.plus.clicked.connect(lambda _=False: self.action.emit("nudge-up"))
        self.pan.clicked.connect(lambda _=False: self.action.emit("pan"))
        self.frame.clicked.connect(lambda _=False: self.action.emit("frame"))
        self.ink_text.clicked.connect(lambda _=False: self.action.emit("ink-text"))
        self.undo.clicked.connect(lambda _=False: self.action.emit("undo"))
        self.clear_btn.clicked.connect(lambda _=False: self.action.emit("clear"))
        self.done.clicked.connect(lambda _=False: self.action.emit("done"))
        self.pill_btn.clicked.connect(lambda _=False: self.expand())
        for name, button in self.shapes.items():
            button.clicked.connect(lambda _checked=False, shape=name: self.action.emit(shape))
        self.width_slider.changed.connect(self.widthChanged.emit)
        self.dim_slider.changed.connect(self.dimChanged.emit)

    def place_initial(self) -> None:
        self.adjustSize()
        screen = QGuiApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        self.move(avail.center().x() - self.width() // 2, avail.bottom() - self.height() - 22)
        self._ready = True

    def expand(self) -> None:
        self._collapsed = False
        self.show()
        if self._state is not None:
            self.apply(self._state)
        self.raise_()

    def collapse(self) -> None:
        self._collapsed = True
        if self._state is not None:
            self.apply(self._state)

    def toggle_collapsed(self) -> None:
        if self._collapsed:
            self.expand()
        else:
            self.collapse()

    def apply(self, state: UiState) -> None:
        anchor = None
        if self._ready:
            geo = self.frameGeometry()
            anchor = QPoint(geo.center().x(), geo.bottom())
        before = self.size()
        self._state = state
        mode = state.mode
        self._set_checked(self.laser, mode == "laser")
        self._set_checked(self.spotlight, mode == "spotlight")
        self._set_checked(self.zoom, mode == "zoom" or state.picking_zoom)
        self._set_checked(self.draw, mode == "draw")
        self._set_checked(self.text, mode == "text")
        self._set_checked(self.pan, mode == "zoom" and not state.inking)
        self._set_checked(self.frame, state.framing)
        for name, button in self.shapes.items():
            active = state.shape == name and (mode == "draw" or (mode == "zoom" and state.inking))
            self._set_checked(button, active)
        self._set_checked(self.ink_text, mode == "zoom" and state.inking and state.shape == "text")
        for dot in self.dots:
            self._set_checked(dot, dot.hex_color.upper() == state.color.upper())

        self.width_slider.blockSignals(True)
        self.width_slider.set_value(state.width)
        self.width_slider.blockSignals(False)
        self.dim_slider.blockSignals(True)
        self.dim_slider.set_value(state.dim)
        self.dim_slider.blockSignals(False)

        show_metric = mode in ("zoom", "lens", "spotlight", "text")
        self.minus.setVisible(show_metric)
        self.plus.setVisible(show_metric)
        self.metric.setVisible(show_metric)
        if mode == "zoom":
            self.metric.setText(format_mag(state.zoom))
        elif mode == "lens":
            self.metric.setText(format_mag(state.lens_power))
        elif mode == "spotlight":
            self.metric.setText(str(int(state.radius)))
        elif mode == "text":
            self.metric.setText(str(state.text_size))

        draw_tools = mode in ("draw", "zoom")
        self.pan.setVisible(mode == "zoom")
        self.frame.setVisible(mode == "spotlight")
        for button in self.shapes.values():
            button.setVisible(draw_tools)
        self.ink_text.setVisible(mode == "zoom")
        self.palette.setVisible(mode in ("draw", "text", "zoom"))
        self.shade.setVisible(mode == "spotlight")
        self.dim_slider.setVisible(mode == "spotlight")
        self.width_slider.setVisible(draw_tools)
        self.undo.setVisible(mode in ("draw", "text", "zoom", "spotlight"))
        self.undo.setEnabled(state.can_undo)
        self.clear_btn.setVisible(mode in ("draw", "text", "zoom", "spotlight"))
        self.done.setVisible(mode != "idle")
        self.hair_a.setVisible(self.palette.isVisible() and (draw_tools or mode == "spotlight" or mode == "text"))
        self.hair_b.setVisible(self.width_slider.isVisible() or self.dim_slider.isVisible())
        self.hair_c.setVisible(self.undo.isVisible())

        hint = state.message or state.hint
        if mode == "idle" and not state.picking_zoom and not state.message and not accessibility_trusted():
            hint = "Activa Accesibilidad para esta app y poder usar los atajos"
        self.hint.setText(hint)
        color = "#E7B15A" if state.message or (mode == "idle" and not state.picking_zoom and not accessibility_trusted()) else "rgba(247,244,236,0.55)"
        self.hint.setStyleSheet(f"color: {color}; background: transparent;")

        if state.picking_zoom:
            self._refresh_zoom_screens()
            for widget in (
                self.minus, self.metric, self.plus, self.pan, self.frame, self.ink_text,
                self.palette, self.shade, self.dim_slider, self.width_slider,
                self.undo, self.clear_btn, self.hair_a, self.hair_b, self.hair_c,
            ):
                widget.hide()
            for button in self.shapes.values():
                button.hide()
            self.screens_box.show()
            self.done.show()
        else:
            self.screens_box.hide()

        self.tools.setVisible(not self._collapsed)
        self.hint.setVisible(not self._collapsed)
        self.context.setVisible(not self._collapsed and (mode != "idle" or state.picking_zoom))
        self._sync_roster()
        self.pill.setVisible(self._collapsed)
        self.adjustSize()
        self.update()
        if anchor is not None and self.size() != before:
            self._move_to_anchor(anchor)

    def _toggle_roster(self, _checked: bool = False) -> None:
        self._roster_open = not self._roster_open
        self._relayout()

    def load_names(self, names: list[str]) -> None:
        self._cancel_spin()
        self._names = [name.strip() for name in names if name.strip()]
        self._pool = list(self._names)
        self._picked = ""
        self._roster_error = "" if self._names else "Ese archivo no tiene nombres"
        self._roster_open = True
        self._relayout()

    def _load_roster(self) -> None:
        self._lower_for_dialog()
        path, _selected = QFileDialog.getOpenFileName(
            self,
            "Cargar listado",
            "",
            "Texto (*.txt);;Todos los archivos (*)",
        )
        self._restore_after_dialog()
        if not path:
            return
        try:
            raw = Path(path).read_bytes()
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
        except OSError:
            self._roster_error = "No se pudo leer el archivo"
            self._relayout()
            return
        self.load_names(names_from_text(text))

    def _pick_student(self) -> None:
        if not self._names or self._spinning:
            return
        if not self._pool:
            self._pool = list(self._names)
        winner = self._pool.pop(random.randrange(len(self._pool)))
        self._picked = winner
        self._spin_frames = spin_sequence(self._names, winner)
        self._spin_index = 0
        self._spinning = True
        self._present_spin(settle=False)
        self._spin_timer.start(_spin_delay(0, len(self._spin_frames)))

    def _spin_tick(self) -> None:
        if not self._spinning:
            return
        self._spin_index += 1
        if self._spin_index >= len(self._spin_frames) - 1:
            self._spin_index = len(self._spin_frames) - 1
            self._spinning = False
            self._present_spin(settle=True)
            return
        self._present_spin(settle=False)
        self._spin_timer.start(_spin_delay(self._spin_index, len(self._spin_frames)))

    def _present_spin(self, *, settle: bool) -> None:
        was_hidden = not self.roster_name.isVisible()
        self._sync_roster()
        if was_hidden or settle:
            self._relayout()

    def _remove_picked(self) -> None:
        if self._spinning or not self._picked:
            return
        name = self._picked
        if name in self._names:
            self._names.remove(name)
        if name in self._pool:
            self._pool.remove(name)
        self._picked = ""
        if not self._names:
            self._pool = []
            self._roster_error = "No quedan nombres"
        self._relayout()

    def _cancel_spin(self) -> None:
        self._spin_timer.stop()
        self._spinning = False
        self._spin_frames = []
        self._spin_index = 0

    def _sync_roster(self) -> None:
        self.roster.setVisible(self._roster_open and not self._collapsed)
        self._set_checked(self.random_btn, self._roster_open)
        self.roster_pick.setVisible(bool(self._names))
        self.roster_pick.setEnabled(bool(self._names) and not self._spinning)
        if self._names:
            count = len(self._names)
            self.roster_status.setText("1 nombre" if count == 1 else f"{count} nombres")
        else:
            self.roster_status.setText(self._roster_error)
        self.roster_status.setVisible(bool(self.roster_status.text()))
        shown = ""
        settled = False
        if self._spinning and self._spin_frames:
            shown = self._spin_frames[min(self._spin_index, len(self._spin_frames) - 1)]
        elif self._picked:
            shown = self._picked
            settled = True
        self.roster_name.setVisible(bool(shown))
        self.roster_remove.setVisible(settled)
        if shown:
            self.roster_name.setText(shown)
            color = "#E7B15A" if settled else "rgba(247,244,236,0.78)"
            self.roster_name.setStyleSheet(f"color: {color}; background: transparent;")

    def _relayout(self) -> None:
        anchor = None
        if self._ready:
            geo = self.frameGeometry()
            anchor = QPoint(geo.center().x(), geo.bottom())
        before = self.size()
        self._sync_roster()
        self.adjustSize()
        self.update()
        if anchor is not None and self.size() != before:
            self._move_to_anchor(anchor)

    def _lower_for_dialog(self) -> None:
        self._flags_before_dialog = self.windowFlags()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()
        set_native_level(self, 0)

    def _restore_after_dialog(self) -> None:
        if self._flags_before_dialog is not None:
            self.setWindowFlags(self._flags_before_dialog)
            self._flags_before_dialog = None
        self.show()
        self.apply_native()
        self.raise_()

    def _refresh_zoom_screens(self) -> None:
        screens = QGuiApplication.screens()
        signature = tuple(
            (screen.name(), screen.geometry().x(), screen.geometry().y(), screen.geometry().width(), screen.geometry().height())
            for screen in screens
        )
        if signature == self._zoom_screens:
            return
        self._zoom_screens = signature
        while self._zoom_screen_row.count():
            item = self._zoom_screen_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        for index, screen in enumerate(screens):
            button = TextButton(_screen_label(screen))
            button.clicked.connect(lambda _=False, i=index: self.action.emit(f"zoom-screen-{i}"))
            self._zoom_screen_row.addWidget(button)

    def _move_to_anchor(self, anchor: QPoint) -> None:
        screen = QGuiApplication.screenAt(anchor) or QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        x = anchor.x() - self.width() // 2
        y = anchor.y() - self.height()
        x = max(avail.left() + 8, min(x, avail.right() - self.width() - 8))
        y = max(avail.top() + 8, min(y, avail.bottom() - self.height() - 8))
        self.move(x, y)

    @staticmethod
    def _set_checked(button, checked: bool) -> None:
        button.blockSignals(True)
        button.setChecked(checked)
        button.blockSignals(False)
