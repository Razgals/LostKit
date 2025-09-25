# styles.py
import os

# Dark Pastel Theme Colors - GREY THEME
DARK_PASTEL_GREY = "#3a3a3a"      # Main dark pastel grey  
DARKER_GREY = "#2a2a2a"           # Darker grey for backgrounds
LIGHTER_GREY = "#4a4a4a"          # Slightly lighter grey
MEDIUM_GREY = "#505050"           # Medium grey for hover states
DARK_PASTEL_RED = "#8b4a4a"       # Dark pastel red for accents
LIGHTER_RED = "#a55a5a"           # Slightly lighter red
TEXT_COLOR = "#f5e6c0"            # Light beige text
BORDER_COLOR = "#2a2a2a"          # Dark border
ACTIVE_TAB_COLOR = "#3a3a3a"      # Dark grey for active tab (was green)
INACTIVE_TAB_COLOR = "#4a4a4a"    # Light grey for inactive tabs

MAIN_STYLESHEET = f"""
QMainWindow {{
    color: {TEXT_COLOR};
    background-color: #000000;
}}

/* Set all widgets to black background */
QWidget {{
    background-color: #000000;
    color: {TEXT_COLOR};
    font-family: 'RuneScape UF', 'runescape_uf', 'Arial', sans-serif;
    font-size: 14px;  /* Increased from 13px to 14px */
}}

/* Force RuneScape font on all text elements */
QLabel, QPushButton, QCheckBox, QGroupBox, QTabWidget, QTabBar {{
    font-family: 'RuneScape UF', 'runescape_uf', 'Arial', sans-serif;
}}

/* Tab Widget Styling - Simple and Clean */
QTabWidget::pane {{
    border: 2px solid {BORDER_COLOR};
    border-radius: 0px;
    background-color: #000000;
}}

QTabWidget::tab-bar {{
    font-family: 'RuneScape UF', 'runescape_uf', 'Arial', sans-serif;
}}

QTabBar::tab {{
    font-family: 'RuneScape UF', 'runescape_uf', 'Arial', sans-serif;
    font-weight: bold;
    font-size: 13px;  /* Increased from 12px to 13px */
    background-color: {INACTIVE_TAB_COLOR};
    border: 2px solid {BORDER_COLOR};
    border-radius: 0px;
    padding: 6px 14px;
    margin: 1px;
    min-width: 80px;
    max-height: 32px;
    color: {TEXT_COLOR};
}}

/* Active/Selected Tab - Dark Grey */
QTabBar::tab:selected {{
    background-color: {ACTIVE_TAB_COLOR};
    border-color: {BORDER_COLOR};
    color: {TEXT_COLOR};
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background-color: {LIGHTER_GREY};
    border-color: {DARK_PASTEL_RED};
}}

/* Force font on window titles and all text */
* {{
    font-family: 'RuneScape UF', 'runescape_uf', 'Arial', sans-serif;
}}

QSplitter {{
    background-color: #000000;
}}

QSplitter::handle {{
    background-color: {BORDER_COLOR};
    width: 4px;
}}

QSplitter::handle:hover {{
    background-color: {DARK_PASTEL_RED};
}}

/* Tool Panel Styling - BLACK backgrounds */
QScrollArea {{
    background-color: #000000;
    border: 2px solid {BORDER_COLOR};
    border-radius: 0px;
}}

QScrollArea > QWidget {{
    background-color: #000000;
}}

QScrollArea > QWidget > QWidget {{
    background-color: #000000;
}}

QScrollBar:vertical {{
    background-color: {DARKER_GREY};
    width: 16px;
    border: 1px solid {BORDER_COLOR};
    border-radius: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {DARK_PASTEL_RED};
    border: 1px solid {BORDER_COLOR};
    border-radius: 0px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {LIGHTER_RED};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    background-color: {DARKER_GREY};
    border: 1px solid {BORDER_COLOR};
    height: 16px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background-color: {DARKER_GREY};
}}

/* Default Tool Buttons - SHARP EDGES - SMALLER */
QPushButton {{
    background-color: {DARK_PASTEL_RED};
    border: 2px solid {BORDER_COLOR};
    border-radius: 0px;
    padding: 8px 10px;  /* Reduced padding */
    color: {TEXT_COLOR};
    font-weight: bold;
    font-size: 13px;
    min-height: 40px;  /* Reduced from 45px to 40px */
    max-height: 45px;  /* Reduced from 50px to 45px */
    text-align: center;
}}

QPushButton:hover {{
    background-color: {LIGHTER_RED};
    border-color: {DARK_PASTEL_RED};
}}

QPushButton:pressed {{
    background-color: {DARK_PASTEL_RED};
    border: 2px inset {BORDER_COLOR};
}}

/* Settings Panel - BLACK background */
QGroupBox {{
    color: {TEXT_COLOR};
    font-weight: bold;
    font-size: 15px;  /* Increased from 14px to 15px */
    border: 2px solid {BORDER_COLOR};
    border-radius: 0px;
    margin: 8px 0px;
    padding-top: 10px;
    background-color: #000000;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 10px 0 10px;
    font-size: 15px;  /* Increased from 14px to 15px */
    background-color: {DARKER_GREY};
}}

/* BOTH Checkboxes RED - External and FPS */
QCheckBox {{
    color: {TEXT_COLOR};
    spacing: 8px;
    font-size: 14px;  /* Increased from 13px to 14px */
    background-color: #000000;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
}}

QCheckBox::indicator:unchecked {{
    background-color: {LIGHTER_GREY};
    border: 2px solid {BORDER_COLOR};
    border-radius: 0px;
}}

/* ALL checkboxes use RED when checked */
QCheckBox::indicator:checked {{
    background-color: {DARK_PASTEL_RED};
    border: 2px solid {BORDER_COLOR};
    border-radius: 0px;
}}

/* Tool Windows */
QWebEngineView {{
    border: 2px solid {BORDER_COLOR};
}}
"""

def get_icon_path(tool_name):
    """Return the path to PNG icon for a tool, with fallback to emoji"""
    # Map tool names to their corresponding PNG file names
    icon_file_map = {
        "Clue Coordinates": "coordinates.png",
        "Clue Scroll Help": "cluehelp.png", 
        "World Map": "worldmap.png",
        "Highscores": "highscores.png",
        "Market Prices": "market.png",
        "Quest Help": "quests.png",
        "Skill Guides": "skillsguides.png",
        "Forums": "forums.png",
        "Skills Calculator": "skillscalculator.png",
        "Bestiary": "bestiary.png",
        "Lost City": "LostCity.png"  # Added Lost City icon mapping
    }
    
    # Get the PNG file name for this tool
    filename = icon_file_map.get(tool_name)
    if filename:
        # Check if the icons folder and file exist
        icon_path = os.path.join("icons", filename)
        if os.path.exists(icon_path):
            return icon_path
    
    # Fallback to emoji if PNG not found
    emoji_map = {
        "Clue Coordinates": "🗺",
        "Clue Scroll Help": "📜", 
        "World Map": "🗺️",
        "Highscores": "🏆",
        "Market Prices": "💰",
        "Quest Help": "🛡️",
        "Skill Guides": "📚",
        "Forums": "💬",
        "Skills Calculator": "🧮",
        "Bestiary": "🐉",
        "Lost City": "⚔️"  # Updated emoji for Lost City
    }
    return emoji_map.get(tool_name, "🔧")

def get_tool_urls():
    """Return mapping of tool names to their URLs"""
    return {
        "Forums": "https://lostcity.rs",
        "Clue Coordinates": "https://razgals.github.io/2004-Coordinates/",
        "Clue Scroll Help": "https://razgals.github.io/Treasure/",
        "World Map": "https://2004.lostcity.rs/worldmap", 
        "Highscores": "https://2004.lostcity.rs/hiscores",
        "Market Prices": "https://lostcity.markets",
        "Quest Help": "https://2004.losthq.rs/?p=questguides",
        "Skill Guides": "https://2004.losthq.rs/?p=skillguides",
        "Skills Calculator": "https://2004.losthq.rs/?p=calculators",
        "Bestiary": "https://2004.losthq.rs/?p=droptables"
    }