"""LensFlow Design System - Color Palette

Defines all color tokens, glassmorphism translucent gradients, and QColor helpers.
"""

from PySide6.QtGui import QColor

# Base Palette
BG_PRIMARY = "#0B0B0F"
SURFACE = "#14141A"
ELEVATED = "#1C1C22"
ELEVATED_HOVER = "#24242C"
BORDER = "rgba(255, 255, 255, 0.08)"
BORDER_SUBTLE = "rgba(255, 255, 255, 0.05)"

# Accent Colors
ACCENT = "#3B82F6"          # Electric Blue
ACCENT_HOVER = "#60A5FA"    # Light Electric Blue
ACCENT_PRESSED = "#1D4ED8"  # Dark Electric Blue
ACCENT_GLOW = "rgba(59, 130, 246, 0.25)"

# Status Colors
DANGER = "#EF4444"          # Muted Red
DANGER_HOVER = "#F87171"
SUCCESS = "#10B981"         # Muted Green
SUCCESS_HOVER = "#34D399"
WARNING = "#F59E0B"         # Muted Amber

# Typography Colors
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#9CA3AF"
TEXT_MUTED = "#6B7280"
TEXT_DISABLED = "#4B5563"

# Glassmorphism Tokens
GLASS_BG = "rgba(20, 20, 26, 0.65)"
GLASS_BG_HOVER = "rgba(28, 28, 34, 0.80)"
GLASS_BORDER = "rgba(255, 255, 255, 0.12)"
GLASS_BORDER_HOVER = "rgba(255, 255, 255, 0.22)"
GLASS_SHADOW = "rgba(0, 0, 0, 0.45)"


def get_qcolor(hex_or_rgba: str) -> QColor:
    """Helper to convert hex string or rgba string to PySide6 QColor object."""
    if hex_or_rgba.startswith("rgba"):
        parts = hex_or_rgba.replace("rgba(", "").replace(")", "").split(",")
        r, g, b = int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip())
        a = float(parts[3].strip())
        return QColor(r, g, b, int(a * 255))
    return QColor(hex_or_rgba)
