from ui_sub_widgets.splitter import StyledSplitter
from ui_sub_widgets.list_base import ListBase
from ui_sub_widgets.settings_tile import SettingsTile
import os
import json
from PyQt6.QtCore import Qt, QFileInfo
from PyQt6.QtWidgets import QListWidgetItem, QPushButton, QSizePolicy, QFileDialog, QFileIconProvider, QMessageBox
from ui_sub_widgets.program_item import ProgramItem

class FloatingWidgetMenuMain(StyledSplitter):
    def __init__(self, parent=None):
        super().__init__(parent, orientation=Qt.Orientation.Vertical)
        self.setHandleWidth(parent.splitter_height)
        self.setChildrenCollapsible(False)
        self.setSizes([(parent.WIDGET_HEIGHT-parent.splitter_height-parent.notch_height)//2, (parent.WIDGET_HEIGHT-parent.splitter_height-parent.notch_height)//2])
        self.setContentsMargins(int(parent.splitter_height*1.5), int(parent.splitter_height*1.5), 0, int(parent.splitter_height*1.5))
        
        # Programs
        self.programs_area = ListBase(self, label="Programs", sz=74)
        self.programs_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'programs.json')
        self._load_programs()
        self._add_plus_button()
        # Settings
        self.settings_tiles = {}
        settings_area = ListBase(self, parent.main_radius - (parent.splitter_height*2.4), label="Auto Settings", sz=92)
        self.settings_tiles["wifi"] = SettingsTile(0, "\uE1D8", "\uE1DA", ["On", "Off"], 2, "WiFi", "wifi", settings_area.list_widget)
        self.settings_tiles["bt"] = SettingsTile(0, "\uE1A7", "\uE1A9", ["On", "Off"], 2, "Bluetooth", "bt", settings_area.list_widget)
        self.settings_tiles["brightness"] = SettingsTile(1, "\uE1AC", "\uE1AD", [], 0, "Brightness", "brightness", settings_area.list_widget)
        self.settings_tiles["volume"] = SettingsTile(1, "\uE050", "\uE04F", [], 0, "Volume", "volume", settings_area.list_widget)
        self.settings_tiles["performance"] = SettingsTile(0, "\uE322", "\uE4FF",  ["High", "Medium", "Low"], 3, "Performance Mode", "performance", settings_area.list_widget)
        self.settings_tiles["nightlight"] = SettingsTile(0, "\uF34F", "\uEB76", ["On", "Off"], 2, "Night Light", "nightlight", settings_area.list_widget)
        self.settings_tiles["airplane"] = SettingsTile(0, "\uE195", "\uE194", ["On", "Off"], 2, "Airplane Mode", "airplane", settings_area.list_widget)
        self.settings_tiles["notifications"] = SettingsTile(0, "\uE7F7", "\uE7F6", ["On", "Off"], 2, "Notifications", "notifications", settings_area.list_widget)
        self.settings_tiles["hotspot"] = SettingsTile(0, "\uE1E2", "\uE0CE", ["On", "Off"], 2, "Hotspot", "hotspot", settings_area.list_widget)
        self.settings_tiles["systemcolor"] = SettingsTile(0, "\uEB37", "\uEC72", ["Light", "Dark"], 2, "System Color", "systemcolor", settings_area.list_widget)
        self.settings_tiles["mic"] = SettingsTile(0, "\uE029", "\uE02B", ["On", "Off"], 2, "Microphone", "mic", settings_area.list_widget)
        self.settings_tiles["priority"] = SettingsTile(2, "\uE7FD", "\uE510", [], 0, "Priority", "priority", settings_area.list_widget)
        
        self.addWidget(self.programs_area)
        self.addWidget(settings_area)
        
        self.selected_program = None
        self.programs_area.list_widget.currentItemChanged.connect(self._on_program_selected)

        if hasattr(settings_area, 'btn'):
            settings_area.btn.clicked.connect(self._on_save_settings)

    def _add_plus_button(self):
        plus_item = QListWidgetItem()
        plus_button = QPushButton("+")
        plus_button.setStyleSheet('''QPushButton {
                                  font-size: 18px; color: #aaa; background: transparent;
                                  }
                                  QPushButton:pressed, QPushButton:checked, QPushButton:hover, QPushButton:focus {
                                  background: transparent; border: none; outline: none;
                                  }''')
        plus_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        plus_button.clicked.connect(self._on_add_program)
        lw = self.programs_area.list_widget
        lw.addItem(plus_item)
        lw.setItemWidget(plus_item, plus_button)
        self.plus_item = plus_item

    def _on_add_program(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Executables (*.exe)")
        if file_dialog.exec():
            exe_path = file_dialog.selectedFiles()[0]
            exe_name = os.path.splitext(os.path.basename(exe_path))[0]
            # Prevent duplicate by full exe path
            lw = self.programs_area.list_widget
            for i in range(lw.count()):
                item = lw.item(i)
                if hasattr(item, 'path') and os.path.normcase(os.path.abspath(item.path)) == os.path.normcase(os.path.abspath(exe_path)):
                    QMessageBox.warning(self, "Duplicate Program", f"This program is already in the list.")
                    return
            icon_provider = QFileIconProvider()
            icon = icon_provider.icon(QFileInfo(exe_path))
            # When adding a new program, initialize settings
            default_settings = {k: {"tile_value": 0, "is_unchanged": True} for k in self.settings_tiles.keys()}
            prog_item = ProgramItem(
                name=exe_name,
                path=exe_path,
                priority=-1,
                icon=icon,
                settings=default_settings
            )
            # Insert before the plus button
            lw.insertItem(lw.count()-1, prog_item)
            self.selected_program = prog_item
            self._on_program_selected(prog_item, None)
            self._save_programs()

    def _load_programs(self):
        if os.path.exists(self.programs_json_path):
            with open(self.programs_json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
            icon_provider = QFileIconProvider()
            for entry in data:
                icon = icon_provider.icon(QFileInfo(entry['path'])) if os.path.exists(entry['path']) else None
                prog_item = ProgramItem(
                    name=entry['name'],
                    path=entry['path'],
                    priority=entry.get('priority', -1),
                    icon=icon,
                    settings=entry.get('settings', {}),
                    parent_list=self.programs_area.list_widget
                )
                self.programs_area.add_item(prog_item)

    def _save_programs(self):
        lw = self.programs_area.list_widget
        programs = []
        for i in range(lw.count()):
            item = lw.item(i)
            # Skip the plus button
            if lw.itemWidget(item):
                continue
            if hasattr(item, 'name') and hasattr(item, 'path'):
                programs.append({
                    'name': item.name,
                    'path': item.path,
                    'priority': item.priority,
                    'settings': getattr(item, 'settings', {})
                })
        with open(self.programs_json_path, 'w', encoding='utf-8') as f:
            json.dump(programs, f, indent=2)

    def _on_program_selected(self, current, previous):
        if current is None or not hasattr(current, 'settings'):
            # No program selected, zero/unchange all tiles
            for tile in self.settings_tiles.values():
                tile.set_state(0, True)
            self.selected_program = None
            return
        self.selected_program = current
        for key, tile in self.settings_tiles.items():
            state = current.settings.get(key, {"tile_value": 0, "is_unchanged": True})
            tile.set_state(state["tile_value"], state["is_unchanged"])

    def _on_save_settings(self):
        if not self.selected_program:
            return
        for key, tile in self.settings_tiles.items():
            self.selected_program.settings[key] = tile.get_state()
        self._save_programs()