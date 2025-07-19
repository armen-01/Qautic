from PyQt6.QtGui import QColor, QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
import winaccent
from json_handler import load_preferences

def update_all_widgets(parent):
    if hasattr(parent, 'update_style'):
        parent.update_style()
    parent.update()
    for child in parent.findChildren(QWidget):
        if hasattr(child, 'update_style'):
            child.update_style()
        child.update()

def adjust_color(hex_color, delta):
    c = QColor(hex_color)
    r = max(0, min(255, c.red() + delta))
    g = max(0, min(255, c.green() + delta))
    b = max(0, min(255, c.blue() + delta))
    return f"#{r:02x}{g:02x}{b:02x}"


def get_luminance(hex_color: str) -> float:
    c = QColor(hex_color)
    return (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255.0

def invert_pixmap_colors(pixmap: QPixmap) -> QPixmap:
    image = pixmap.toImage()
    image.invertPixels(QImage.InvertMode.InvertRgb)
    inverted_pixmap = QPixmap.fromImage(image)
    return inverted_pixmap

def colorize_pixmap(pixmap: QPixmap, color: QColor = None) -> QPixmap:
    if color is None:
        color = QColor(FONT)
    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), color)
    painter.end()
    return result

def load_theme_preferences_and_update_colors():
    global BASE_BG, BASE_BACK_DARK, MAIN_BG, SPLITTER, ELEMENT_LIGHT, SLIDER_FILLED, SLIDER_BAR, FONT, FONT_INACTIVE, HIDE_BTN_INACTIVE, HIDE_BTN_ACTIVE, ADD_BUTTON, ITEM_SELECTED_BG, LIST_BTN
    # Load preferences
    prefs = load_preferences()
    theme = prefs.get('theme', 'dark')
    use_system_color = prefs.get('use_system_color', False)
    # Determine BASE_BG
    if use_system_color:
        if theme == 'light' or winaccent.system_uses_light_theme is True:
            BASE_BG = winaccent.accent_light_2
        else:
            BASE_BG = winaccent.accent_dark_2
    else:
        if theme == 'light' or winaccent.system_uses_light_theme is True:
            BASE_BG = "#777777"
        else:
            BASE_BG = "#2C2C2C"
    # Recalculate all derived colors
    BASE_BACK_DARK = adjust_color(BASE_BG, -16 if get_luminance(BASE_BG) < 0.5 else 16)
    MAIN_BG = adjust_color(BASE_BG, 16 if get_luminance(BASE_BG) < 0.5 else -16)
    SPLITTER = adjust_color(BASE_BG, 18 if get_luminance(BASE_BG) < 0.5 else -18)
    ELEMENT_LIGHT = adjust_color(BASE_BG, 35 if get_luminance(BASE_BG) < 0.5 else -35)
    SLIDER_FILLED = adjust_color(BASE_BG, 60 if get_luminance(BASE_BG) < 0.5 else -60)
    SLIDER_BAR = adjust_color(BASE_BG, 100 if get_luminance(BASE_BG) < 0.5 else -100)
    FONT = adjust_color(BASE_BG, 180 if get_luminance(BASE_BG) < 0.5 else -150)
    FONT_INACTIVE = adjust_color(BASE_BG, 55 if get_luminance(BASE_BG) < 0.5 else -55)
    HIDE_BTN_INACTIVE = adjust_color(BASE_BG, 60 if get_luminance(BASE_BG) < 0.5 else -60)
    HIDE_BTN_ACTIVE = adjust_color(BASE_BG, 85 if get_luminance(BASE_BG) < 0.5 else -85)
    ADD_BUTTON = adjust_color(BASE_BG, 54 if get_luminance(BASE_BG) < 0.5 else -54)
    ITEM_SELECTED_BG = adjust_color(BASE_BG, 41 if get_luminance(BASE_BG) < 0.5 else -41)
    LIST_BTN = adjust_color(BASE_BG, 75 if get_luminance(BASE_BG) < 0.5 else -75)

load_theme_preferences_and_update_colors()