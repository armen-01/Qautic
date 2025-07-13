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
        settings_area = ListBase(self, parent.main_radius - (parent.splitter_height*2.4), label="Auto Settings", sz=92)
        tile_wifi = SettingsTile(0, "\uE1D8", "\uE1DA", ["On", "Off"], 2, "WiFi", settings_area.list_widget)
        tile_bt = SettingsTile(0, "\uE1A7", "\uE1A9", ["On", "Off"], 2, "Bluetooth", settings_area.list_widget)
        tile_brightness = SettingsTile(1, "\uE1AC", "\uE1AD", [], 0, "Brightness", settings_area.list_widget)
        tile_volume = SettingsTile(1, "\uE050", "\uE04F", [], 0, "Volume", settings_area.list_widget)
        tile_performance = SettingsTile(0, "\uE322", "\uE4FF",  ["High", "Medium", "Low"], 3, "Performance Mode", settings_area.list_widget)
        tile_nightlight = SettingsTile(0, "\uF34F", "\uEB76", ["On", "Off"], 2, "Night Light", settings_area.list_widget)
        tile_airplane = SettingsTile(0, "\uE195", "\uE194", ["On", "Off"], 2, "Airplane Mode", settings_area.list_widget)
        tile_notifications = SettingsTile(0, "\uE7F7", "\uE7F6", ["On", "Off"], 2, "Notifications", settings_area.list_widget)
        tile_hotspot = SettingsTile(0, "\uE1E2", "\uE0CE", ["On", "Off"], 2, "Hotspot", settings_area.list_widget)
        tile_systemcolor = SettingsTile(0, "\uEB37", "\uEC72", ["Light", "Dark"], 2, "System Color", settings_area.list_widget)
        tile_mic = SettingsTile(0, "\uE029", "\uE02B", ["On", "Off"], 2, "Microphone", settings_area.list_widget)
        tile_priority = SettingsTile(2, "\uE7FD", "\uE510", [], 0, "Priority", settings_area.list_widget)
        
        self.addWidget(self.programs_area)
        self.addWidget(settings_area)

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
            prog_item = ProgramItem(
                name=exe_name,
                path=exe_path,
                priority=-1,
                icon=icon,
                parent_list=self.programs_area.list_widget
            )
            # Insert before the plus button
            lw.insertItem(lw.count()-1, prog_item)
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
                    'priority': item.priority
                })
        with open(self.programs_json_path, 'w', encoding='utf-8') as f:
            json.dump(programs, f, indent=2)