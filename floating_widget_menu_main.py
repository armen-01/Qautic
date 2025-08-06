from ui_sub_widgets.splitter import StyledSplitter
from ui_sub_widgets.list_base import ListBase
from ui_sub_widgets.settings_tile import SettingsTile
import os
from PyQt6.QtCore import Qt, QFileInfo
from PyQt6.QtWidgets import QListWidgetItem, QPushButton, QSizePolicy, QFileDialog, QFileIconProvider, QMessageBox
from ui_sub_widgets.program_item import ProgramItem
import ui_colors
from floating_widget_default_item import default_settings_item
from json_handler import load_preferences, save_preferences, load_programs, save_programs

class FloatingWidgetMenuMain(StyledSplitter):
    def __init__(self, parent=None):
        super().__init__(parent, orientation=Qt.Orientation.Vertical)
        self.setHandleWidth(parent.splitter_height)
        self.setChildrenCollapsible(False)
        self.setSizes([(parent.WIDGET_HEIGHT-parent.splitter_height-parent.notch_height)//2, (parent.WIDGET_HEIGHT-parent.splitter_height-parent.notch_height)//2])
        self.setContentsMargins(int(parent.splitter_height*1.5), int(parent.splitter_height*1.5), 0, int(parent.splitter_height*1.5))
        
        self.programs_area = ListBase(self, label="Programs", sz=74)
        
        self.settings_tiles = {}
        self.settings_area = ListBase(self, parent.main_radius - (parent.splitter_height*2.4), label="Auto Settings", sz=92)
        self._create_settings_tiles()

        self._load_programs()
        self.add_item, self.plus_button = self._add_plus_button()
        default_settings = self._load_default_settings()
        self.default_item, self.default_settings_label = default_settings_item(self, default_settings)

        self.addWidget(self.programs_area)
        self.addWidget(self.settings_area)
        
        self.selected_program = None
        self.programs_area.list_widget.currentItemChanged.connect(self._on_program_selected)

        # Connect signals for tile interactions
        self.settings_tiles["airplane"].user_interacted.connect(self._on_airplane_mode_changed)
        self.settings_tiles["wifi"].user_interacted.connect(self._on_radio_dependency_changed)
        self.settings_tiles["hotspot"].user_interacted.connect(self._on_radio_dependency_changed)

        if hasattr(self.settings_area, 'btn'):
            self.settings_area.btn.clicked.connect(self._on_save_settings)
        if hasattr(self.programs_area, 'btn'):
            self.programs_area.btn.clicked.connect(self._on_clear_programs)
        
        self.update_style()

    def _create_settings_tiles(self):
        tiles_data = [
            ("wifi", 0, "\uE1D8", "\uE1DA", ["On", "Off"], 2, "WiFi"),
            ("bt", 0, "\uE1A7", "\uE1A9", ["On", "Off"], 2, "Bluetooth"),
            ("brightness", 1, "\uE1AC", "\uE1AD", [], 0, "Brightness"),
            ("volume", 1, "\uE050", "\uE04F", [], 0, "Volume"),
            ("performance", 0, "\uE322", "\uE4FF",  ["High", "Medium", "Low"], 3, "Performance Mode"),
            ("nightlight", 0, "\uF34F", "\uEB76", ["On", "Off"], 2, "Night Light"),
            ("airplane", 0, "\uE195", "\uE194", ["On", "Off"], 2, "Airplane Mode"),
            ("microphone", 0, "\uE029", "\uE02b", ["On", "Off"], 2, "Microphone"),
            ("hotspot", 0, "\uE1E2", "\uE0CE", ["On", "Off"], 2, "Hotspot"),
            ("systemcolor", 0, "\uEB37", "\uEC72", ["Light", "Dark"], 2, "System Color"),
            ("startup", 0, "\uEB9B", "\uEBA5", ["On", "Off"], 2, "Launch at System Startup"),
            ("priority", 2, "\uE7FD", "\uE510", [], 0, "Priority")
        ]
        for key, type_, on, off, opts, count, tip in tiles_data:
            self.settings_tiles[key] = SettingsTile(type_, on, off, opts, count, tip, key, self.settings_area.list_widget)

    def update_style(self):
        if hasattr(self, 'plus_button'):
            self.plus_button.setStyleSheet(f'QPushButton {{ font-size: 18px; color: {ui_colors.ADD_BUTTON}; background: transparent; }}')
        if hasattr(self, 'default_settings_label'):
            self.default_settings_label.setStyleSheet(f"color: {ui_colors.ADD_BUTTON};")

    def _add_plus_button(self):
        plus_item = QListWidgetItem()
        plus_button = QPushButton("+")
        plus_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        plus_button.clicked.connect(self._on_add_program)
        lw = self.programs_area.list_widget
        lw.addItem(plus_item)
        lw.setItemWidget(plus_item, plus_button)
        return plus_item, plus_button

    def _on_add_program(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Executables (*.exe)")
        if file_dialog.exec():
            exe_path = file_dialog.selectedFiles()[0]
            exe_name = os.path.splitext(os.path.basename(exe_path))[0]
            lw = self.programs_area.list_widget
            for i in range(lw.count()):
                item = lw.item(i)
                if hasattr(item, 'path') and item.path != "internal::default" and os.path.normcase(os.path.abspath(item.path)) == os.path.normcase(os.path.abspath(exe_path)):
                    QMessageBox.warning(self, "Duplicate Program", f"This program is already in the list.")
                    return
            icon_provider = QFileIconProvider()
            icon = icon_provider.icon(QFileInfo(exe_path))
            default_settings = {k: {"tile_value": 0, "is_unchanged": True} for k in self.settings_tiles.keys()}
            prog_item = ProgramItem(name=exe_name, path=exe_path, icon=icon, settings=default_settings, parent_list=lw)
            lw.insertItem(lw.count() - 2, prog_item) # Insert before add button and default item
            lw.setCurrentItem(prog_item)
            self._save_programs()

    def _load_programs(self):
        data = load_programs()
        icon_provider = QFileIconProvider()
        for entry in data:
            icon = icon_provider.icon(QFileInfo(entry['path'])) if os.path.exists(entry['path']) else None
            is_enabled = entry.get('is_enabled', True)
            prog_item = ProgramItem(
                name=entry['name'], 
                path=entry['path'], 
                icon=icon, 
                settings=entry.get('settings', {}), 
                parent_list=self.programs_area.list_widget,
                is_enabled=is_enabled
            )
            self.programs_area.add_item(prog_item)

    def _save_programs(self):
        lw = self.programs_area.list_widget
        programs = []
        for i in range(lw.count()):
            item = lw.item(i)
            if isinstance(item, ProgramItem) and item.path != "internal::default":
                programs.append({
                    'name': item.name, 
                    'path': item.path, 
                    'settings': getattr(item, 'settings', {}),
                    'is_enabled': getattr(item, 'is_enabled', True)
                })
        save_programs(programs)

    def _load_default_settings(self):
        prefs = load_preferences()
        default_settings = prefs.get('default_settings', {k: {"tile_value": 0, "is_unchanged": True} for k in self.settings_tiles.keys()})
        return default_settings

    def _save_default_settings(self):
        prefs = load_preferences()
        prefs['default_settings'] = self.selected_program.settings
        save_preferences(prefs)

    def _on_program_selected(self, current, previous):
        if current == self.add_item:
            self.selected_program = None
            self.settings_area.setEnabled(False)
            for tile in self.settings_tiles.values():
                tile.set_state(0, True)
        else:
            self.settings_area.setEnabled(True)
            self.selected_program = current
            
            for tile in self.settings_tiles.values():
                tile.widget.blockSignals(True)
            try:
                for key, tile in self.settings_tiles.items():
                    state = current.settings.get(key, {"tile_value": 0, "is_unchanged": True})
                    tile.set_state(state["tile_value"], state["is_unchanged"])
            finally:
                for tile in self.settings_tiles.values():
                    tile.widget.blockSignals(False)

            is_default_item = (current == self.default_item)
            self.settings_tiles["priority"].setEnabled(not is_default_item)
            if is_default_item:
                priority_state = self.selected_program.settings.get("priority", {"tile_value": 0, "is_unchanged": True})
                priority_state["is_unchanged"] = True
                self.settings_tiles["priority"].set_state(priority_state["tile_value"], priority_state["is_unchanged"])

            self._on_airplane_mode_changed()
            self._on_radio_dependency_changed(None)

    def _on_save_settings(self):
        if not self.selected_program: return
        
        for key, tile in self.settings_tiles.items():
            self.selected_program.settings[key] = tile.get_state()
        
        if self.selected_program == self.default_item:
            self._save_default_settings()
        else:
            self._save_programs()

    def _on_clear_programs(self):
        lw = self.programs_area.list_widget
        items_to_remove = []
        for i in range(lw.count()):
            item = lw.item(i)
            if isinstance(item, ProgramItem) and item.path != "internal::default":
                items_to_remove.append(item)
        
        for item in items_to_remove:
            lw.takeItem(lw.row(item))
            
        self._save_programs()
        lw.setCurrentItem(self.default_item)

    def _on_airplane_mode_changed(self):
        if not self.selected_program or self.selected_program == self.add_item:
            return
        airplane_state = self.settings_tiles["airplane"].get_state()
        is_on = airplane_state["tile_value"] == 0 and not airplane_state["is_unchanged"]
        
        self.settings_tiles["wifi"].setEnabled(not is_on)
        self.settings_tiles["bt"].setEnabled(not is_on)
        self.settings_tiles["hotspot"].setEnabled(not is_on)
        
        if is_on:
            self.settings_tiles["wifi"].set_state(0, True)
            self.settings_tiles["bt"].set_state(0, True)
            self.settings_tiles["hotspot"].set_state(0, True)

    def _on_radio_dependency_changed(self, source_key):
        if not self.selected_program or self.selected_program == self.add_item:
            return

        hotspot_tile = self.settings_tiles["hotspot"]
        wifi_tile = self.settings_tiles["wifi"]

        hotspot_tile.widget.blockSignals(True)
        wifi_tile.widget.blockSignals(True)

        try:
            hotspot_state = hotspot_tile.get_state()
            wifi_state = wifi_tile.get_state()

            if source_key == 'hotspot':
                if not hotspot_state['is_unchanged'] and hotspot_state['tile_value'] == 0:
                    if wifi_state['is_unchanged'] or wifi_state['tile_value'] == 1:
                        wifi_tile.set_state(0, False)

            elif source_key == 'wifi':
                if not wifi_state['is_unchanged'] and wifi_state['tile_value'] == 1:
                    if not hotspot_state['is_unchanged'] and hotspot_state['tile_value'] == 0:
                        hotspot_tile.set_state(0, True)
        finally:
            hotspot_tile.widget.blockSignals(False)
            wifi_tile.widget.blockSignals(False)
