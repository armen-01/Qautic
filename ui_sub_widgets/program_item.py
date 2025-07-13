from PyQt6.QtWidgets import QListWidgetItem, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

class ProgramItem(QListWidgetItem):
    def __init__(self, name: str, path: str, priority: int, icon: QIcon = None, parent_list=None):
        super().__init__(name)
        self.name = name
        self.path = path
        self.priority = priority
        self.is_enabled = True
        self._original_icon = icon
        self.setToolTip(name)
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
        menu.addAction(delete_action)
        menu.exec(event.globalPosition().toPoint())

    def remove_from_json(self):
        # Traverse up: QListWidget -> ListBase -> FloatingWidgetMenuMain
        list_widget = self.parent_list
        if list_widget is None:
            #print("No parent_list set on ProgramItem!")
            return
        list_base = list_widget.parentWidget() if hasattr(list_widget, 'parentWidget') else None
        if not list_base:
            #print("No ListBase parent found!")
            return
        main_widget = list_base.parentWidget() if hasattr(list_base, 'parentWidget') else None
        if not main_widget or not hasattr(main_widget, 'programs_json_path'):
            #print(f"No valid parent with programs_json_path! main_widget={main_widget}")
            return
        json_path = main_widget.programs_json_path
        import json, os
        #print(f"Attempting to write to: {json_path}")
        if not os.path.exists(json_path):
            #print("JSON path does not exist!")
            return
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            #print(f"Error reading JSON: {e}")
            data = []
        new_data = [entry for entry in data if not (entry.get('name') == self.name and entry.get('path') == self.path)]
        if len(new_data) != len(data):
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2)
                #print("Wrote to JSON!")
            except Exception as e:
                print(f"Error writing JSON: {e}")
        # else:
        #     print("No change to JSON.")

        # Optionally, update parent's in-memory list if needed
        if hasattr(main_widget, '_save_programs'):
            main_widget._save_programs()
