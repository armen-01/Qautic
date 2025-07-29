from PyQt6.QtWidgets import QListWidgetItem, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

class ProgramItem(QListWidgetItem):
    def __init__(self, name: str, path: str, icon: QIcon = None, settings=None, parent_list=None, is_enabled=True):
        super().__init__(name)
        self.name = name
        self.path = path
        self.is_enabled = is_enabled
        self._original_icon = icon
        self.setToolTip(name)
        self.settings = settings or {}  # Dict of {setting_key: {tile_value, is_unchanged}}
        self.parent_list = parent_list  # Reference to the parent QListWidget
        if icon:
            self.setIcon(icon)
        self.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._update_icon_appearance()

    def _update_icon_appearance(self):
        font = self.font()
        if not self.is_enabled:
            font.setStrikeOut(True)
        else:
            font.setStrikeOut(False)
        self.setFont(font)

    def toggle_enabled(self):
        self.is_enabled = not self.is_enabled
        self._update_icon_appearance()
        self._save_state_to_json()

    def set_enabled(self, enabled: bool):
        self.is_enabled = enabled
        self._update_icon_appearance()

    def handle_mouse_event(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

    def show_context_menu(self, event):
        # Find the parent QListWidget
        list_widget = self.listWidget() if hasattr(self, 'listWidget') else self.parent_list
        if list_widget is None:
            return
        menu = QMenu()
        # Enable/Disable action
        toggle_action_text = "Enable" if not self.is_enabled else "Disable"
        toggle_action = QAction(toggle_action_text, menu)

        toggle_action.triggered.connect(self.toggle_enabled)
        menu.addAction(toggle_action)
        # Delete action
        delete_action = QAction("Delete", menu)
        def delete():
            row = list_widget.row(self)
            list_widget.takeItem(row)
            # Remove from JSON
            self.remove_from_json()
        delete_action.triggered.connect(delete)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(event.globalPosition().toPoint())

    def _save_state_to_json(self):
        # Traverse up: QListWidget -> ListBase -> FloatingWidgetMenuMain
        list_widget = self.parent_list
        if list_widget is None: return
        list_base = list_widget.parentWidget() if hasattr(list_widget, 'parentWidget') else None
        if not list_base: return
        main_widget = list_base.parentWidget() if hasattr(list_base, 'parentWidget') else None
        if not main_widget or not hasattr(main_widget, '_save_programs'): return
        # Call _save_programs after toggling to sync JSON
        main_widget._save_programs()

    def remove_from_json(self):
        # Traverse up: QListWidget -> ListBase -> FloatingWidgetMenuMain
        list_widget = self.parent_list
        if list_widget is None:
            return
        list_base = list_widget.parentWidget() if hasattr(list_widget, 'parentWidget') else None
        if not list_base:
            return
        main_widget = list_base.parentWidget() if hasattr(list_base, 'parentWidget') else None
        if not main_widget or not hasattr(main_widget, '_save_programs'):
            return
        # Call _save_programs after removing from UI to sync JSON
        main_widget._save_programs()
