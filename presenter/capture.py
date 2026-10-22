"""Capture the desktop under Presenter so zoom never photographs itself."""

from __future__ import annotations

import sys

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QGuiApplication, QImage, QPixmap
from PyQt6.QtWidgets import QApplication


def screen_recording_allowed() -> bool:
    """True when a capture will include other apps, not just the desktop background.

    Without Screen Recording, macOS still returns an image, but every window is
    removed. That flat background is the black screen Zoom was magnifying.
    """
    if sys.platform != "darwin":
        return True
    try:
        from Quartz import CGPreflightScreenCaptureAccess

        return bool(CGPreflightScreenCaptureAccess())
    except Exception:
        return True


def capture_screen(screen) -> QPixmap:
    if screen is None or not screen_recording_allowed():
        return QPixmap()
    if sys.platform == "darwin":
        pixmap = _capture_quartz(screen.geometry(), None)
        if not pixmap.isNull():
            return pixmap
    pixmap = screen.grabWindow(0)
    return pixmap if pixmap is not None else QPixmap()


def capture_region(rect: QRect, below_window: int | None = None) -> QPixmap:
    if rect.width() < 2 or rect.height() < 2 or not screen_recording_allowed():
        return QPixmap()
    if sys.platform == "darwin":
        pixmap = _capture_quartz(rect, below_window)
        if not pixmap.isNull():
            return pixmap
    return _capture_qt(rect)


def _capture_qt(rect: QRect) -> QPixmap:
    screen = QGuiApplication.screenAt(rect.center())
    if screen is None:
        screen = QApplication.primaryScreen()
    if screen is None:
        return QPixmap()
    origin = screen.geometry().topLeft()
    local = rect.translated(-origin.x(), -origin.y())
    return screen.grabWindow(0, local.x(), local.y(), local.width(), local.height())


def _capture_quartz(rect: QRect, below_window: int | None) -> QPixmap:
    try:
        from Quartz import (
            CGDataProviderCopyData,
            CGImageGetBytesPerRow,
            CGImageGetDataProvider,
            CGImageGetHeight,
            CGImageGetWidth,
            CGRectMake,
            CGWindowListCreateImage,
            kCGNullWindowID,
            kCGWindowImageDefault,
            kCGWindowListOptionOnScreenBelowWindow,
            kCGWindowListOptionOnScreenOnly,
        )
    except Exception:
        return QPixmap()

    if below_window:
        option = kCGWindowListOptionOnScreenBelowWindow
        window_id = below_window
    else:
        option = kCGWindowListOptionOnScreenOnly
        window_id = kCGNullWindowID
    image = CGWindowListCreateImage(
        CGRectMake(rect.x(), rect.y(), rect.width(), rect.height()),
        option,
        window_id,
        kCGWindowImageDefault,
    )
    if image is None:
        return QPixmap()
    width = int(CGImageGetWidth(image))
    height = int(CGImageGetHeight(image))
    if width < 2 or height < 2:
        return QPixmap()
    row_bytes = int(CGImageGetBytesPerRow(image))
    provider = CGImageGetDataProvider(image)
    data = CGDataProviderCopyData(provider)
    raw = bytearray(data)
    if len(raw) < height * row_bytes:
        return QPixmap()
    qimage = QImage(raw, width, height, row_bytes, QImage.Format.Format_ARGB32_Premultiplied)
    qimage = qimage.copy()
    if rect.width() > 0:
        qimage.setDevicePixelRatio(width / rect.width())
    return QPixmap.fromImage(qimage)
