"""
Draws the Wield icon and writes assets/icons/wield.png (512px) and
assets/icons/wield.ico (16-256px, for the .exe and taskbar).

    python -m tools.make_icon

The mark: the brand violet in a rounded square, a white "W" drawn like the
path of a moving hand (round caps and joins), and a dot above the middle
peak, like a fingertip.
"""

import os
import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPainterPath, QPen

VIOLET = "#7857FC"
WHITE = "#FFFFFF"

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons")


def draw_icon(size):

    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    p = QPainter(image)
    p.setRenderHint(QPainter.Antialiasing)

    s = float(size)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(VIOLET))
    p.drawRoundedRect(QRectF(0, 0, s, s), s * 0.23, s * 0.23)

    w = QPainterPath(QPointF(s * 0.20, s * 0.34))
    for x, y in ((0.355, 0.72), (0.50, 0.45), (0.645, 0.72), (0.80, 0.34)):
        w.lineTo(QPointF(s * x, s * y))

    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(WHITE), s * 0.105, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPath(w)

    p.setPen(Qt.NoPen)
    p.setBrush(QColor(WHITE))
    p.drawEllipse(QPointF(s * 0.50, s * 0.235), s * 0.06, s * 0.06)

    p.end()
    return image


def main():

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    os.makedirs(OUT_DIR, exist_ok=True)

    png = os.path.join(OUT_DIR, "wield.png")
    draw_icon(512).save(png)

    # Pillow writes a proper multi-size .ico from the large PNG.
    from PIL import Image
    Image.open(png).save(
        os.path.join(OUT_DIR, "wield.ico"),
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    print("Wrote", png, "and wield.ico")


if __name__ == "__main__":
    main()
