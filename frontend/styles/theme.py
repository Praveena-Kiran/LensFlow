"""
LensFlow - Design System & Theme Constants

Centralized color tokens and styling utilities unified around the LensFlow brand identity:
- Dark neutral foundation (#08090D background, #101118 surface, #171923 hover, #252936 border)
- Indigo / Violet primary brand accent (#7C5CFF, hover #8B70FF)
- Secondary Accent (#5B8CFF)
- Restrained semantic colors (Green #22C55E, Yellow #F59E0B, Red #EF4444)
- Crisp typography hierarchy (#F5F5F7 primary text, #8B93A7 secondary text)
"""

# ============================================================================
# COLOR PALETTE
# ============================================================================

# Surface & Background Hierarchy
BG_DARK = "#08090D"           # Neutral dark background
SURFACE = "#101118"           # Main surface / card background
SURFACE_HOVER = "#171923"     # Surface on hover
SURFACE_ACTIVE = "#1D202D"    # Active / pressed surface
SURFACE_OVERLAY = "#141520"   # Modals & floating panels

# Border Tokens
BORDER = "#252936"            # Default neutral border
BORDER_SUBTLE = "#1E222D"     # Extremely subtle border
BORDER_HOVER = "rgba(124, 92, 255, 0.35)"  # Brand hover glow
BORDER_FOCUS = "#7C5CFF"      # Focus state border

# Primary Brand (Indigo / Violet)
PRIMARY = "#7C5CFF"           # LensFlow Primary Brand
PRIMARY_HOVER = "#8B70FF"     # Hover brightness
PRIMARY_PRESSED = "#6845EC"   # Pressed state
PRIMARY_MUTED = "rgba(124, 92, 255, 0.15)" # Subtle brand background tint

# Secondary Accent
SECONDARY_ACCENT = "#5B8CFF"  # Blue-Indigo
SECONDARY_ACCENT_HOVER = "#739EFF"
SECONDARY_ACCENT_MUTED = "rgba(91, 140, 255, 0.15)"

# Brand Variations for Studio Icons (Subtle spectrum of the brand palette)
ACCENT_INDIGO = "#6875F5"
ACCENT_BLUE_INDIGO = "#5B8CFF"
ACCENT_VIOLET = "#8B5CF6"
ACCENT_PURPLE_INDIGO = "#7C5CFF"

# Semantic Status Colors (Only used for meaningful communication)
SUCCESS = "#22C55E"           # Connected / ready / success
WARNING = "#F59E0B"           # Idle / warning
ERROR = "#EF4444"             # Destructive / error
INFO = "#5B8CFF"              # Informational state

# Typography Colors
PRIMARY_TEXT = "#F5F5F7"      # Headings & primary labels
SECONDARY_TEXT = "#8B93A7"    # Descriptions & sub-labels
TEXT_MUTED = "#646B7E"        # Metadata / timestamps
TEXT_DISABLED = "#474D5E"     # Disabled state

# ============================================================================
# COMPATIBILITY ALIASES
# ============================================================================

TEXT_PRIMARY = PRIMARY_TEXT
TEXT_SECONDARY = SECONDARY_TEXT
SURFACE_CARD = SURFACE
SURFACE_ELEVATED = SURFACE_HOVER
SURFACE_ROOT = BG_DARK
BORDER_DEFAULT = BORDER
ACCENT_BLUE = PRIMARY
ACCENT_PURPLE = PRIMARY
STATUS_GREEN = SUCCESS
STATUS_AMBER = WARNING
STATUS_RED = ERROR

# ============================================================================
# COMMON QSS MIXINS
# ============================================================================

CARD_FRAME_STYLE = f"""
    QFrame#StudioCard {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 16px;
    }}
    QFrame#StudioCard:hover {{
        background-color: {SURFACE_HOVER};
        border: 1px solid {BORDER_HOVER};
    }}
"""

BUTTON_PRIMARY_STYLE = f"""
    QPushButton {{
        background-color: {PRIMARY};
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        padding: 6px 14px;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {PRIMARY_PRESSED};
    }}
"""

BUTTON_SECONDARY_STYLE = f"""
    QPushButton {{
        background-color: rgba(255, 255, 255, 0.04);
        color: {PRIMARY_TEXT};
        border: 1px solid {BORDER};
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        padding: 6px 12px;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.16);
        color: #FFFFFF;
    }}
    QPushButton:pressed {{
        background-color: rgba(255, 255, 255, 0.03);
    }}
"""

BUTTON_DESTRUCTIVE_STYLE = f"""
    QPushButton {{
        background-color: rgba(239, 68, 68, 0.10);
        color: {ERROR};
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        padding: 6px 12px;
    }}
    QPushButton:hover {{
        background-color: rgba(239, 68, 68, 0.20);
        border: 1px solid rgba(239, 68, 68, 0.40);
        color: #FCA5A5;
    }}
    QPushButton:pressed {{
        background-color: rgba(239, 68, 68, 0.28);
    }}
"""

MENU_STYLE = f"""
    QMenu {{
        background-color: {SURFACE};
        color: {PRIMARY_TEXT};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 14px;
        border-radius: 6px;
        font-size: 12px;
    }}
    QMenu::item:selected {{
        background-color: {PRIMARY_MUTED};
        color: #FFFFFF;
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {BORDER};
        margin: 4px 6px;
    }}
"""
