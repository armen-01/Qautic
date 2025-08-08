from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle, QColorDialog
from PyQt6.QtGui import QIcon, QAction, QActionGroup
from ui_colors import load_theme_preferences_and_update_colors, update_all_widgets
from json_handler import load_preferences, save_preferences, get_asset_path
import os

class TrayIcon(QSystemTrayIcon):
    def __init__(self, floating_widget, parent=None):
        super().__init__(parent)
        self.floating_widget = floating_widget
        self.slider_value = 74

        # Set custom icon
        icon_path = os.path.join(get_asset_path(), 'assets', 'graphics', 'ico.png')
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # Fallback to a default system icon if the custom one isn't found
            app = QApplication.instance()
            if app is not None:
                default_icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
                self.setIcon(default_icon)
            else:
                self.setIcon(QIcon())
        
        self.setToolTip('Show/Hide Floating Widget')

        # Create context menu
        menu = QMenu()
        # Theme submenu
        theme_menu = QMenu("Theme", menu)
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        self.action_theme_light = QAction("Light", theme_menu, checkable=True)
        self.action_theme_dark = QAction("Dark", theme_menu, checkable=True)
        self.action_theme_auto = QAction("Auto", theme_menu, checkable=True)
        theme_group.addAction(self.action_theme_light)
        theme_group.addAction(self.action_theme_dark)
        theme_group.addAction(self.action_theme_auto)
        theme_menu.addAction(self.action_theme_light)
        theme_menu.addAction(self.action_theme_dark)
        theme_menu.addAction(self.action_theme_auto)
        theme_menu.addSeparator()

        # Color source submenu
        color_group = QActionGroup(self)
        color_group.setExclusive(True)
        self.action_color_system = QAction("System Color", self, checkable=True)
        self.action_color_custom = QAction("Custom Color", self, checkable=True)
        self.action_color_none = QAction("No Color", self, checkable=True)
        color_group.addAction(self.action_color_system)
        color_group.addAction(self.action_color_custom)
        color_group.addAction(self.action_color_none)
        theme_menu.addAction(self.action_color_system)
        theme_menu.addAction(self.action_color_custom)
        theme_menu.addAction(self.action_color_none)

        menu.addMenu(theme_menu)
        self.toggle_service_action = QAction('Disable Service', self)
        self.toggle_service_action.triggered.connect(self._toggle_service_status)
        quit_action = QAction('Quit', self)
        menu.addAction(self.toggle_service_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

        quit_action.triggered.connect(self.quit_app)
        self.activated.connect(self.on_activated)
        # Connect theme actions to save logic
        self.action_theme_light.triggered.connect(lambda: self.set_theme_pref('light'))
        self.action_theme_dark.triggered.connect(lambda: self.set_theme_pref('dark'))
        self.action_theme_auto.triggered.connect(lambda: self.set_theme_pref('auto'))
        
        # Connect color source actions
        self.action_color_system.triggered.connect(lambda: self.set_color_source_pref('system'))
        self.action_color_custom.triggered.connect(self.set_custom_color)
        self.action_color_none.triggered.connect(lambda: self.set_color_source_pref('none'))

        # Load preferences on startup
        self.load_theme_preferences()
        self._load_service_status()

    def show_widget(self):
        self.floating_widget.slide_in()

    def hide_widget(self):
        self.floating_widget.slide_out()

    def quit_app(self):
        self.floating_widget.close()
        self.hide()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.floating_widget.isVisible():
                self.floating_widget.slide_out()
            else:
                self.floating_widget.slide_in()

    def _update_theme(self):
        load_theme_preferences_and_update_colors()
        update_all_widgets(self.floating_widget)

    def set_theme_pref(self, theme):
        prefs = load_preferences()
        prefs['theme'] = theme
        save_preferences(prefs)
        self.action_theme_light.setChecked(theme == 'light')
        self.action_theme_dark.setChecked(theme == 'dark')
        self.action_theme_auto.setChecked(theme == 'auto')
        self._update_theme()

    def set_color_source_pref(self, source):
        prefs = load_preferences()
        prefs['color_source'] = source
        save_preferences(prefs)
        self.action_color_system.setChecked(source == 'system')
        self.action_color_custom.setChecked(source == 'custom')
        self.action_color_none.setChecked(source == 'none')
        self._update_theme()

    def set_custom_color(self):
        prefs = load_preferences()
        from PyQt6.QtGui import QColor
        
        # Use the single custom_color for initial selection
        initial_color_hex = prefs.get('custom_color', '#777777')
        initial_color = QColor(initial_color_hex)
        
        # Use self.floating_widget as parent for QColorDialog
        color = QColorDialog.getColor(initial_color, self.floating_widget, "Select Custom Color")
        
        if color.isValid():
            prefs['custom_color'] = color.name()
            save_preferences(prefs)
            self.set_color_source_pref('custom')

    def load_theme_preferences(self):
        prefs = load_preferences()
        theme = prefs.get('theme', 'auto')
        color_source = prefs.get('color_source', 'none')
        
        self.action_theme_light.setChecked(theme == 'light')
        self.action_theme_dark.setChecked(theme == 'dark')
        self.action_theme_auto.setChecked(theme == 'auto')
        
        self.action_color_system.setChecked(color_source == 'system')
        self.action_color_custom.setChecked(color_source == 'custom')
        self.action_color_none.setChecked(color_source == 'none')

    def _load_service_status(self):
        prefs = load_preferences()
        is_enabled = prefs.get('service_enabled', True)  # Default to enabled
        self.toggle_service_action.setText("Disable Service" if is_enabled else "Enable Service")

    def _toggle_service_status(self):
        prefs = load_preferences()
        is_enabled = prefs.get('service_enabled', True)
        new_state = not is_enabled
        prefs['service_enabled'] = new_state
        save_preferences(prefs)
        self.toggle_service_action.setText("Disable Service" if new_state else "Enable Service")

