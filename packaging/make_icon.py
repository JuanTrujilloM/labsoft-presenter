"""Draw the Presenter mark and write a macOS icon."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath
from PyQt6.QtWidgets import QApplication

from presenter.icons import paint_icon

HERE = Path(__file__).resolve().parent
SIZES = (16, 32, 128, 256, 512)


def render(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = QRectF(0, 0, size, size)
    path = QPainterPath()
    radius = size * 0.22
    path.addRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
    painter.fillPath(path, QColor(22, 22, 24))
    margin = size * 0.16
    paint_icon(painter, "mark", rect.adjusted(margin, margin, -margin, -margin), QColor("#F7F4EC"))
    painter.end()
    return image


def main() -> int:
    app = QApplication(sys.argv)
    iconset = HERE / "Presenter.iconset"
    iconset.mkdir(exist_ok=True)
    for size in SIZES:
        image = render(size)
        image.save(str(iconset / f"icon_{size}x{size}.png"))
        if size <= 512:
            image = render(size * 2)
            image.save(str(iconset / f"icon_{size}x{size}@2x.png"))
    icns = HERE / "Presenter.icns"
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)], check=True)
    app.exit(0)
    print(icns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
