"""Launch Presenter."""

from __future__ import annotations

import sys


def main() -> int:
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication

    from presenter.app import Presenter
    from presenter.theme import app_stylesheet, ui_font

    app = QApplication(sys.argv)
    app.setApplicationName("Presenter")
    app.setApplicationDisplayName("Presenter")
    app.setOrganizationName("Presenter")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setFont(ui_font(13, QFont.Weight.Normal))
    app.setStyleSheet(app_stylesheet())

    presenter = Presenter()
    presenter.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
