"""LensFlow Design System - Typography

Reusable typography tokens and QFont helper utilities.
"""

from typing import NamedTuple
from PySide6.QtGui import QFont

FONT_FAMILY_PRIMARY = "Inter, SF Pro Display, -apple-system, Segoe UI, sans-serif"
FONT_FAMILY_MONO = "JetBrains Mono, SF Mono, Consolas, monospace"


class TypographySpec(NamedTuple):
    size: int
    weight: QFont.Weight
    line_height: float
    letter_spacing: float


# Typography Hierarchy Constants
DISPLAY = TypographySpec(size=28, weight=QFont.Weight.Bold, line_height=1.2, letter_spacing=-0.5)
HEADING = TypographySpec(size=20, weight=QFont.Weight.DemiBold, line_height=1.3, letter_spacing=-0.3)
TITLE = TypographySpec(size=15, weight=QFont.Weight.DemiBold, line_height=1.4, letter_spacing=-0.2)
BODY = TypographySpec(size=13, weight=QFont.Weight.Normal, line_height=1.5, letter_spacing=0.0)
CAPTION = TypographySpec(size=11, weight=QFont.Weight.Medium, line_height=1.4, letter_spacing=0.1)
BUTTON = TypographySpec(size=13, weight=QFont.Weight.DemiBold, line_height=1.0, letter_spacing=0.2)


def get_font(spec: TypographySpec, family: str = FONT_FAMILY_PRIMARY) -> QFont:
    """Returns a configured PySide6 QFont instance for the given TypographySpec."""
    font = QFont(family, spec.size)
    font.setWeight(spec.weight)
    font.setPointSizeF(float(spec.size))
    return font


def get_font_qss(spec: TypographySpec) -> str:
    """Returns QSS string representation for CSS font properties."""
    weight_val = 700 if spec.weight >= QFont.Weight.Bold else (600 if spec.weight >= QFont.Weight.DemiBold else (500 if spec.weight >= QFont.Weight.Medium else 400))
    return f"font-size: {spec.size}px; font-weight: {weight_val}; letter-spacing: {spec.letter_spacing}px;"
