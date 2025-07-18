from PyQt6.QtWidgets import QListWidgetItem, QLabel, QSizePolicy, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup
import os
import json
import ui_colors

# Preferences utility functions
def _get_preferences_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'preferences.json'))

def _load_preferences():
    pref_path = _get_preferences_path()
    try:
        with open(pref_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_preferences(prefs):
    pref_path = _get_preferences_path()
    try:
        with open(pref_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2)
    except Exception as e:
        print(f"Error saving preferences: {e}")

def default_settings_item(self):
    default_settings = QListWidgetItem()
    def_lbl = QLabel("Default")
    def_lbl.setStyleSheet(f"color: {ui_colors.ADD_BUTTON};")
    def_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    def_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    font = self.programs_area.font
    font.setPointSize(10)
    def_lbl.setFont(font)
    lw = self.programs_area.list_widget
    lw.addItem(default_settings)
    lw.setItemWidget(default_settings, def_lbl)

    def_lbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def get_default_pref():
        prefs = _load_preferences()
        return prefs.get('default_settings_option', 'fallback')

    def set_default_pref(option):
        prefs = _load_preferences()
        prefs['default_settings_option'] = option
        _save_preferences(prefs)

    def _on_context_menu(point):
        menu = QMenu(def_lbl)
        group = QActionGroup(menu)
        group.setExclusive(True)
        default_use = QAction("Use Defaults", menu, checkable=True)
        default_disable = QAction("Disable Defaults", menu, checkable=True)
        default_fallback = QAction("Fall Back", menu, checkable=True)
        group.addAction(default_use)
        group.addAction(default_disable)
        group.addAction(default_fallback)
        menu.addAction(default_use)
        menu.addAction(default_disable)
        menu.addAction(default_fallback)
        # Load current preference
        current = get_default_pref()
        default_use.setChecked(current == "use")
        default_disable.setChecked(current == "disable")
        default_fallback.setChecked(current == "fallback")
        default_use.triggered.connect(lambda: set_default_pref("use"))
        default_disable.triggered.connect(lambda: set_default_pref("disable"))
        default_fallback.triggered.connect(lambda: set_default_pref("fallback"))
        menu.exec(def_lbl.mapToGlobal(point))

    def_lbl.customContextMenuRequested.connect(_on_context_menu)