from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QFont, QFontDatabase, QMouseEvent
import os
import ui_colors

class HideButton(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts', 'MaterialSymbolsRounded-VariableFont_FILL,GRAD,opsz,wght.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        font = QFont(font_families[5])
        font.setPointSize(25)
        self.setFont(font)
        self.setText("\uEAC9") #\uE15A
        self.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.setStyleSheet(f"color: {ui_colors.HIDE_BTN_INACTIVE}; background: transparent;")
        self._hover = False

    def enterEvent(self, event):
        self._hover = True
        self.setStyleSheet(f"color: {ui_colors.HIDE_BTN_ACTIVE}; background: transparent;")

    def leaveEvent(self, event):
        self._hover = False
        self.setStyleSheet(f"color: {ui_colors.HIDE_BTN_INACTIVE}; background: transparent;")

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent().slide_out()