from PyQt6.QtGui import QColor, QPixmap, QImage

def adjust_color(hex_color, delta):
    c = QColor(hex_color)
    r = max(0, min(255, c.red() + delta))
    g = max(0, min(255, c.green() + delta))
    b = max(0, min(255, c.blue() + delta))
    return f"#{r:02x}{g:02x}{b:02x}"

BASE_BG = "#2C2C2C"
BASE_BACK_DARK = adjust_color(BASE_BG, -16)
MAIN_BG = adjust_color(BASE_BG, 16)
SPLITTER = adjust_color(BASE_BG, 18)
ELEMENT_LIGHT = adjust_color(BASE_BG, 35)
SLIDER_FILLED = adjust_color(BASE_BG, 60)
SLIDER_BAR = adjust_color(BASE_BG, 100)
FONT = adjust_color(BASE_BG, 18*10)
FONT_INACTIVE = adjust_color(BASE_BG, 55)
HIDE_BTN_INACTIVE = adjust_color(BASE_BG, 60)
HIDE_BTN_ACTIVE = adjust_color(BASE_BG, 85)
ADD_BUTTON = adjust_color(BASE_BG, 54)
ITEM_SELECTED_BG = adjust_color(BASE_BG, 41)

def invert_pixmap_colors(pixmap: QPixmap) -> QPixmap:
    image = pixmap.toImage()
    image.invertPixels(QImage.InvertMode.InvertRgb)
    inverted_pixmap = QPixmap.fromImage(image)
    return inverted_pixmap