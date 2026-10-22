"""Keep Presenter above slides, including fullscreen presentation spaces."""

from __future__ import annotations

import sys

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QWidget

_LEVEL: int | None = None


def screen_saver_level() -> int:
    global _LEVEL
    if _LEVEL is not None:
        return _LEVEL
    _LEVEL = 1000
    if sys.platform != "darwin":
        return _LEVEL
    try:
        from Quartz import CGWindowLevelForKey, kCGScreenSaverWindowLevelKey

        _LEVEL = int(CGWindowLevelForKey(kCGScreenSaverWindowLevelKey))
    except Exception:
        _LEVEL = 1000
    return _LEVEL


def prepare_window(widget: QWidget, *, level_offset: int = 0, click_through: bool = False) -> None:
    if sys.platform != "darwin":
        return
    try:
        import objc
        from AppKit import (
            NSColor,
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorIgnoresCycle,
            NSWindowCollectionBehaviorStationary,
        )
    except Exception:
        return
    view = objc.objc_object(c_void_p=int(widget.winId()))
    window = view.window()
    if window is None:
        return
    window.setOpaque_(False)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setHasShadow_(False)
    window.setLevel_(screen_saver_level() + level_offset)
    window.setCollectionBehavior_(
        NSWindowCollectionBehaviorCanJoinAllSpaces
        | NSWindowCollectionBehaviorFullScreenAuxiliary
        | NSWindowCollectionBehaviorIgnoresCycle
        | NSWindowCollectionBehaviorStationary
    )
    window.setHidesOnDeactivate_(False)
    window.setIgnoresMouseEvents_(bool(click_through))


def window_number(widget: QWidget) -> int | None:
    if sys.platform != "darwin" or not widget.isVisible():
        return None
    try:
        import objc

        view = objc.objc_object(c_void_p=int(widget.winId()))
        window = view.window()
        if window is None:
            return None
        return int(window.windowNumber())
    except Exception:
        return None


def activate_app() -> None:
    if sys.platform != "darwin":
        return
    try:
        from AppKit import NSApplication

        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    except Exception:
        pass


def accessibility_trusted() -> bool:
    if sys.platform != "darwin":
        return True
    try:
        from ApplicationServices import AXIsProcessTrusted

        return bool(AXIsProcessTrusted())
    except Exception:
        return True


def request_accessibility() -> None:
    if sys.platform != "darwin":
        return
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt

        AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
    except Exception:
        pass


def request_screen_recording() -> None:
    if sys.platform != "darwin":
        return
    try:
        from Quartz import CGRequestScreenCaptureAccess

        CGRequestScreenCaptureAccess()
    except Exception:
        pass


class FloatingWindow(QWidget):
    """Frameless translucent window that can float over a fullscreen slide."""

    level_offset = 2

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._click_through = False

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        QTimer.singleShot(0, self.apply_native)

    def apply_native(self) -> None:
        prepare_window(self, level_offset=self.level_offset, click_through=self._click_through)

    def set_click_through(self, enabled: bool) -> None:
        self._click_through = enabled
        if self.isVisible():
            self.apply_native()
