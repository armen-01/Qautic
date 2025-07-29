from PyQt6.QtWidgets import QListWidgetItem, QLabel, QSizePolicy, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup
import ui_colors
from json_handler import load_preferences, save_preferences

def default_settings_item(parent_widget, settings):
    default_item = QListWidgetItem()
    default_item.settings = settings # Attach settings to the item
    
    def_lbl = QLabel("Default")
    def_lbl.setStyleSheet(f"color: {ui_colors.ADD_BUTTON};")
    def_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    def_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    font = parent_widget.programs_area.font
    font.setPointSize(10)
    def_lbl.setFont(font)
    
    lw = parent_widget.programs_area.list_widget
    lw.addItem(default_item)
    lw.setItemWidget(default_item, def_lbl)

    def_lbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def get_default_pref():
        prefs = load_preferences()
        return prefs.get('default_settings_option', 'use')

    def set_default_pref(option):
        prefs = load_preferences()
        prefs['default_settings_option'] = option
        save_preferences(prefs)

    def _on_context_menu(point):
        menu = QMenu(def_lbl)
        group = QActionGroup(menu)
        group.setExclusive(True)
        default_use = QAction("Use Defaults", menu, checkable=True)
        default_disable = QAction("Disable Defaults", menu, checkable=True)
        #default_fallback = QAction("Fall Back", menu, checkable=True)
        group.addAction(default_use)
        group.addAction(default_disable)
        #group.addAction(default_fallback)
        menu.addAction(default_use)
        menu.addAction(default_disable)
        #menu.addAction(default_fallback)
        current = get_default_pref()
        default_use.setChecked(current == "use")
        default_disable.setChecked(current == "disable")
        #default_fallback.setChecked(current == "fallback")
        default_use.triggered.connect(lambda: set_default_pref("use"))
        default_disable.triggered.connect(lambda: set_default_pref("disable"))
        #default_fallback.triggered.connect(lambda: set_default_pref("fallback"))
        menu.exec(def_lbl.mapToGlobal(point))

    def_lbl.customContextMenuRequested.connect(_on_context_menu)
    return default_item, def_lbl