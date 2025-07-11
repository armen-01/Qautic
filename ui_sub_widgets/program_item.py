from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt

class ProgramItem(QListWidgetItem):
    def __init__(self, name: str, path: str, priority: int, icon: QIcon = None):
        super().__init__(name)
        self.name = name
        self.path = path
        self.priority = priority
        self.is_enabled = True
        self._original_icon = icon
        self.setToolTip(name)
        if icon:
            self.setIcon(icon)
        self.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._update_icon_appearance()

    def _update_icon_appearance(self):
        # Dim the icon
        if self._original_icon:
            if not self.is_enabled:
                pixmap = self._original_icon.pixmap(256,256, mode=QIcon.Mode.Normal, state=QIcon.State.Off)
                from PyQt6.QtGui import QPainter
                dimmed = pixmap.copy()
                painter = QPainter(dimmed)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
                painter.fillRect(dimmed.rect(), QColor(0, 0, 0, 120))
                painter.end()
                self.setIcon(QIcon(dimmed))
            else:
                self.setIcon(self._original_icon)
        # Keep text color the same
        #self.setForeground(QBrush(QColor("#eee")))

    def toggle_enabled(self):
        self.is_enabled = not self.is_enabled
        self._update_icon_appearance()

    def set_enabled(self, enabled: bool):
        self.is_enabled = enabled
        self._update_icon_appearance()

    def handle_mouse_event(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.toggle_enabled()
            print(self.is_enabled)
