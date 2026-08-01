"""
LensFlow Design System
~~~~~~~~~~~~~~~~~~~~~~
Central design tokens, reusable components, and global QSS.

All UI files should import from this module rather than
hardcoding colors or sizes. Components pull live values
from the active theme via `get_theme()`.
"""

from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QWidget
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt

from ui.theme_manager import get_theme


# ─────────────────────────────────────────────
#  DESIGN TOKENS (static constants)
# ─────────────────────────────────────────────

# Spacing scale
SPACE_XS  = 4
SPACE_SM  = 8
SPACE_MD  = 16
SPACE_LG  = 24
SPACE_XL  = 32
SPACE_XXL = 48

# Border radius scale
RADIUS_SM  = 8
RADIUS_MD  = 12
RADIUS_LG  = 16
RADIUS_XL  = 20
RADIUS_PILL = 100   # For fully-rounded pill shapes

# Typography scale (point sizes)
FONT_H1      = 22
FONT_H2      = 16
FONT_H3      = 13
FONT_BODY    = 10
FONT_CAPTION = 8
FONT_FAMILY  = "Segoe UI"


# ─────────────────────────────────────────────
#  FONT HELPERS
# ─────────────────────────────────────────────

def get_font(size=FONT_BODY, bold=False):
    font = QFont(FONT_FAMILY, size)
    if bold:
        font.setBold(True)
    return font


# ─────────────────────────────────────────────
#  GLOBAL QSS STYLESHEET
# ─────────────────────────────────────────────

def get_global_style():
    """
    Returns the application-wide QSS stylesheet.
    Called at startup and on theme changes.
    """
    t = get_theme()

    return f"""
/* ── Base ── */
QMainWindow {{
    background-color: {t.BG_PRIMARY};
}}

QWidget {{
    color: {t.TEXT_PRIMARY};
    font-family: '{FONT_FAMILY}', -apple-system, sans-serif;
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.BORDER_COLOR};
    min-height: 24px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.ACCENT};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {t.BORDER_COLOR};
    min-width: 24px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {t.ACCENT};
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Inputs ── */
QLineEdit {{
    background-color: {t.BG_INPUT};
    border: 1px solid {t.BORDER_COLOR};
    border-radius: {RADIUS_SM}px;
    padding: 8px 12px;
    color: {t.TEXT_PRIMARY};
    selection-background-color: {t.ACCENT};
}}
QLineEdit:focus {{
    border-color: {t.ACCENT};
}}

QTextEdit {{
    background-color: {t.BG_INPUT};
    border: 1px solid {t.BORDER_COLOR};
    border-radius: {RADIUS_SM}px;
    padding: 8px;
    color: {t.TEXT_PRIMARY};
    selection-background-color: {t.ACCENT};
}}
QTextEdit:focus {{
    border-color: {t.ACCENT};
}}

/* ── Combo Box ── */
QComboBox {{
    background-color: {t.BG_INPUT};
    border: 1px solid {t.BORDER_COLOR};
    border-radius: {RADIUS_SM}px;
    padding: 6px 12px;
    color: {t.TEXT_PRIMARY};
    min-height: 20px;
}}
QComboBox:hover {{
    border-color: {t.BORDER_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {t.BG_CARD};
    border: 1px solid {t.BORDER_COLOR};
    border-radius: {RADIUS_SM}px;
    color: {t.TEXT_PRIMARY};
    selection-background-color: {t.ACCENT};
    outline: none;
    padding: 4px;
}}

/* ── Sliders ── */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {t.BG_INPUT};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {t.ACCENT};
    width: 16px;
    height: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {t.ACCENT_HOVER};
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.GRADIENT_START}, stop:1 {t.GRADIENT_END});
    border-radius: 3px;
}}

/* ── Dialogs ── */
QDialog {{
    background-color: {t.BG_PRIMARY};
    color: {t.TEXT_PRIMARY};
}}

/* ── List Widget (for settings nav) ── */
QListWidget {{
    background-color: {t.BG_SURFACE};
    border: 1px solid {t.BORDER_COLOR};
    border-radius: {RADIUS_MD}px;
    color: {t.TEXT_PRIMARY};
    outline: none;
    padding: 4px;
}}
QListWidget::item {{
    padding: 10px 12px;
    border-radius: {RADIUS_SM}px;
    margin: 2px 4px;
}}
QListWidget::item:selected {{
    background-color: {t.ACCENT};
    color: white;
}}
QListWidget::item:hover:!selected {{
    background-color: {t.BG_CARD_HOVER};
}}

/* ── Progress Bar ── */
QProgressBar {{
    border: 1px solid {t.BORDER_COLOR};
    border-radius: 6px;
    background-color: {t.BG_INPUT};
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.ACCENT}, stop:1 {t.SUCCESS});
    border-radius: 5px;
}}

/* ── Tooltips ── */
QToolTip {{
    background-color: {t.BG_CARD};
    color: {t.TEXT_PRIMARY};
    border: 1px solid {t.BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 10px;
}}
"""


# ─────────────────────────────────────────────
#  REUSABLE COMPONENTS
# ─────────────────────────────────────────────

class HoverCard(QFrame):
    """
    Premium card container with soft shadow and
    interactive hover elevation / glow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)

        # Drop shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

        self._apply_normal()

    def _apply_normal(self):
        t = get_theme()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.BG_CARD};
                border-radius: {RADIUS_LG}px;
                border: 1px solid {t.BORDER_COLOR};
            }}
        """)

    def _apply_hover(self):
        t = get_theme()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.BG_CARD_HOVER};
                border-radius: {RADIUS_LG}px;
                border: 1px solid {t.ACCENT};
            }}
        """)

    def enterEvent(self, event):
        self._apply_hover()
        self.shadow.setBlurRadius(32)
        self.shadow.setColor(QColor(124, 58, 237, 45))
        self.shadow.setOffset(0, 8)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_normal()
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.shadow.setOffset(0, 4)
        super().leaveEvent(event)


class ModernButton(QPushButton):
    """
    Polished LensFlow button with three variants:
      - gradient  (hero CTA)
      - primary   (accent fill)
      - default   (subtle outline)
    """
    def __init__(self, text, primary=False, gradient=False, parent=None):
        super().__init__(text, parent)
        t = get_theme()

        self.setFont(get_font(FONT_BODY, bold=True))
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)

        if gradient:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {t.GRADIENT_START},
                        stop:1 {t.GRADIENT_END}
                    );
                    color: #FFFFFF;
                    border-radius: {RADIUS_MD}px;
                    border: none;
                    padding: 0 {SPACE_LG}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {t.ACCENT_HOVER},
                        stop:1 #60A5FA
                    );
                }}
                QPushButton:pressed {{
                    background-color: {t.ACCENT};
                    padding-top: 1px;
                }}
            """)

        elif primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t.ACCENT};
                    color: #FFFFFF;
                    border-radius: {RADIUS_MD}px;
                    border: none;
                    padding: 0 {SPACE_LG}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {t.ACCENT_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {t.GRADIENT_START};
                    padding-top: 1px;
                }}
            """)

        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t.BG_SURFACE};
                    color: {t.TEXT_PRIMARY};
                    border-radius: {RADIUS_MD}px;
                    border: 1px solid {t.BORDER_COLOR};
                    padding: 0 {SPACE_LG}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {t.BG_CARD_HOVER};
                    border-color: {t.BORDER_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {t.BG_INPUT};
                    padding-top: 1px;
                }}
            """)


class SectionHeader(QLabel):
    """
    Standardized uppercase section header used across panels.
    E.g. "TRACKING ENGINE SPECIFICATIONS", "GESTURE TELEMETRY"
    """
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        t = get_theme()
        self.setFont(get_font(FONT_CAPTION, bold=True))
        self.setStyleSheet(f"""
            color: {t.TEXT_MUTED};
            letter-spacing: 1px;
            padding: 0;
            background: transparent;
            border: none;
        """)


class StatusBadge(QLabel):
    """
    Small colored badge for status indicators.
    Variants: 'success', 'active', 'warning', 'danger', 'muted', 'cyan'
    """
    COLORS = {
        "success": ("#10B981", "#FFFFFF"),
        "active":  ("#7C3AED", "#FFFFFF"),
        "cyan":    ("#06B6D4", "#090D16"),
        "warning": ("#F59E0B", "#000000"),
        "danger":  ("#F43F5E", "#FFFFFF"),
        "muted":   ("#1E2640", "#94A3B8"),
    }

    def __init__(self, text, variant="success", parent=None):
        super().__init__(text, parent)
        bg, fg = self.COLORS.get(variant, self.COLORS["muted"])
        self.setFont(get_font(FONT_CAPTION, bold=True))
        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border-radius: {RADIUS_SM}px;
            padding: 4px 12px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """)
        self.setAlignment(Qt.AlignCenter)


class PulseStatusBadge(QFrame):
    """
    Futuristic pill badge showing live system status (ACTIVE / STANDBY)
    with a glowing pulse indicator dot.
    """
    def __init__(self, is_active=True, parent=None):
        super().__init__(parent)
        self.is_active = is_active
        self.setFixedHeight(34)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 14, 4)
        layout.setSpacing(8)
        
        self.dot = QLabel("●")
        self.dot.setFont(get_font(10, bold=True))
        
        self.label = QLabel("SYSTEM ACTIVE" if is_active else "STANDBY MODE")
        self.label.setFont(get_font(9, bold=True))
        
        layout.addWidget(self.dot)
        layout.addWidget(self.label)
        
        self.update_state(is_active)
        
    def update_state(self, is_active):
        self.is_active = is_active
        t = get_theme()
        if is_active:
            dot_color = t.SUCCESS if hasattr(t, 'SUCCESS') else "#10B981"
            bg_color = "rgba(16, 185, 129, 0.15)"
            border_color = "rgba(16, 185, 129, 0.4)"
            text_color = "#34D399"
            self.label.setText("SYSTEM ACTIVE")
        else:
            dot_color = "#F59E0B"
            bg_color = "rgba(245, 158, 11, 0.15)"
            border_color = "rgba(245, 158, 11, 0.4)"
            text_color = "#FBBF24"
            self.label.setText("STANDBY MODE")
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 17px;
            }}
        """)
        self.dot.setStyleSheet(f"color: {dot_color}; border: none; background: transparent;")
        self.label.setStyleSheet(f"color: {text_color}; border: none; background: transparent; letter-spacing: 0.8px;")



# ─────────────────────────────────────────────
#  BACKWARDS COMPATIBILITY EXPORTS
#  (so existing `from ui.theme import X` still works)
# ─────────────────────────────────────────────

def _export_theme_colors():
    """Snapshot current theme values into module-level variables."""
    t = get_theme()
    return {
        "BG_PRIMARY":    t.BG_PRIMARY,
        "BG_SIDEBAR":    t.BG_SIDEBAR,
        "BG_SURFACE":    t.BG_SURFACE,
        "BG_CARD":       t.BG_CARD,
        "BG_CARD_HOVER": t.BG_CARD_HOVER,
        "BG_INPUT":      t.BG_INPUT,
        "ACCENT":        t.ACCENT,
        "ACCENT_HOVER":  t.ACCENT_HOVER,
        "SUCCESS":       t.SUCCESS,
        "DANGER":        t.DANGER,
        "WARNING":       t.WARNING,
        "TEXT_HEADING":  t.TEXT_HEADING,
        "TEXT_PRIMARY":  t.TEXT_PRIMARY,
        "TEXT_MUTED":    t.TEXT_MUTED,
        "BORDER_COLOR":  t.BORDER_COLOR,
        "BORDER_HOVER":  t.BORDER_HOVER,
        "GRADIENT_START": t.GRADIENT_START,
        "GRADIENT_END":  t.GRADIENT_END,
    }

_colors = _export_theme_colors()

BG_PRIMARY    = _colors["BG_PRIMARY"]
BG_SIDEBAR    = _colors["BG_SIDEBAR"]
BG_SURFACE    = _colors["BG_SURFACE"]
BG_CARD       = _colors["BG_CARD"]
BG_CARD_HOVER = _colors["BG_CARD_HOVER"]
BG_INPUT      = _colors["BG_INPUT"]

ACCENT        = _colors["ACCENT"]
ACCENT_HOVER  = _colors["ACCENT_HOVER"]

SUCCESS       = _colors["SUCCESS"]
DANGER        = _colors["DANGER"]
WARNING       = _colors["WARNING"]

TEXT_HEADING  = _colors["TEXT_HEADING"]
TEXT_PRIMARY  = _colors["TEXT_PRIMARY"]
TEXT_MUTED    = _colors["TEXT_MUTED"]

BORDER_COLOR  = _colors["BORDER_COLOR"]
BORDER_HOVER  = _colors["BORDER_HOVER"]

GRADIENT_START = _colors["GRADIENT_START"]
GRADIENT_END   = _colors["GRADIENT_END"]

GLOBAL_STYLE  = get_global_style()

# Legacy creative color aliases
WARM_AMBER = "#F59E0B"
WARM_ROSE  = "#EC4899"