"""
Styles for the mk4 GUI application
"""

# Main window size
WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 1200
MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 480

# Colors
DARK_PRIMARY = "#1e2633"
DARK_SECONDARY = "#2d3748"
DARK_ACCENT = "#4299e1"
DARK_TEXT = "#f7fafc"
DARK_BORDER = "#4a5568"

LIGHT_PRIMARY = "#f7fafc"
LIGHT_SECONDARY = "#edf2f7"
LIGHT_ACCENT = "#3182ce"
LIGHT_TEXT = "#1a202c"
LIGHT_BORDER = "#cbd5e0"

SUCCESS_COLOR = "#48bb78"
ERROR_COLOR = "#f56565"
WARNING_COLOR = "#ed8936"
INFO_COLOR = "#4299e1"

# Theme definitions
THEMES = {
    "light": {
        "primary": LIGHT_PRIMARY,
        "secondary": LIGHT_SECONDARY,
        "accent": LIGHT_ACCENT,
        "text": LIGHT_TEXT,
        "border": LIGHT_BORDER,
        "success": SUCCESS_COLOR,
        "error": ERROR_COLOR,
        "warning": WARNING_COLOR,
        "info": INFO_COLOR,
    },
    "dark": {
        "primary": DARK_PRIMARY,
        "secondary": DARK_SECONDARY,
        "accent": DARK_ACCENT,
        "text": DARK_TEXT,
        "border": DARK_BORDER,
        "success": SUCCESS_COLOR,
        "error": ERROR_COLOR,
        "warning": WARNING_COLOR,
        "info": INFO_COLOR,
    }
}

# Styles for component types
BUTTON_STYLE = """
    QPushButton {
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        opacity: 0.9;
    }
    QPushButton:pressed {
        opacity: 0.8;
    }
    QPushButton:disabled {
        opacity: 0.6;
    }
"""

PROGRESS_BAR_STYLE = """
    QProgressBar {
        text-align: center;
        border-radius: 4px;
        padding: 1px;
        height: 16px;
    }
    QProgressBar::chunk {
        border-radius: 3px;
    }
"""

TEXTBOX_STYLE = """
    QLineEdit, QTextEdit {
        padding: 8px;
        border-radius: 4px;
        border-width: 1px;
        border-style: solid;
    }
"""

COMBOBOX_STYLE = """
    QComboBox {
        padding: 8px;
        border-radius: 4px;
        border-width: 1px;
        border-style: solid;
    }
"""

LIST_VIEW_STYLE = """
    QListView {
        border-radius: 4px;
        border-width: 1px;
        border-style: solid;
        padding: 2px;
    }
"""

# Font sizes
FONT_SMALL = 9
FONT_NORMAL = 10
FONT_LARGE = 12
FONT_XLARGE = 14

# Spacing and margins
MARGIN_SMALL = 8
MARGIN_NORMAL = 12
MARGIN_LARGE = 16

SPACING_SMALL = 5
SPACING_NORMAL = 10
SPACING_LARGE = 15

# Icon sizes
ICON_SMALL = 16
ICON_NORMAL = 24
ICON_LARGE = 32