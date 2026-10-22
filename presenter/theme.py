"""Shared color, type, and spacing for Presenter."""

from __future__ import annotations

import sys

from PyQt6.QtGui import QColor, QFont

ACCENT = QColor("#E7B15A")
ACCENT_SOFT = QColor(231, 177, 90, 42)
IVORY = QColor("#F7F4EC")
IVORY_DIM = QColor(247, 244, 236, 210)
MUTED = QColor(247, 244, 236, 132)
INK = QColor(18, 18, 20, 236)
GLASS = QColor(22, 22, 24, 232)
LINE = QColor(255, 255, 255, 32)
HAIRLINE = QColor(255, 255, 255, 28)

PALETTE = (
    "#FF4D3A",
    "#FFE14A",
    "#F7F4EC",
    "#161616",
    "#3AA0FF",
    "#2FDB8A",
)

DOCK_SHADOW = (18, 12, 18, 20)  # left, top, right, bottom
DOCK_PAD = 8
DOCK_RADIUS = 22


def ui_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont()
    if sys.platform == "darwin":
        font.setFamilies([".AppleSystemUIFont", "Helvetica Neue", "sans-serif"])
    else:
        font.setFamilies(["Segoe UI", "Helvetica Neue", "sans-serif"])
    font.setPointSize(size)
    font.setWeight(weight)
    return font


def format_mag(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return f"{int(round(value))}×"
    return f"{value:.1f}×"


def app_stylesheet() -> str:
    return """
    QToolTip {
        background-color: #1a1a1c;
        color: #F7F4EC;
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 6px 8px;
    }
    QLabel {
        background: transparent;
        color: rgba(247, 244, 236, 0.55);
    }
    """
