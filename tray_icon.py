from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PyQt6.QtGui import QIcon, QAction, QActionGroup
import os
import json

class TrayIcon(QSystemTrayIcon):
    def __init__(self, floating_widget, parent=None):
        super().__init__(parent)
        self.floating_widget = floating_widget
        self.slider_value = 74
        self.preferences_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preferences.json')

        # Set a default icon
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
        self.action_theme_light = QAction("Light", self, checkable=True)
        self.action_theme_dark = QAction("Dark", self, checkable=True)
        self.action_theme_auto = QAction("Auto", self, checkable=True)
        theme_group.addAction(self.action_theme_light)
        theme_group.addAction(self.action_theme_dark)
        theme_group.addAction(self.action_theme_auto)
        theme_menu.addAction(self.action_theme_light)
        theme_menu.addAction(self.action_theme_dark)
        theme_menu.addAction(self.action_theme_auto)
        theme_menu.addSeparator()
        self.action_theme_system = QAction("Use System Color", self, checkable=True)
        theme_menu.addAction(self.action_theme_system)
        menu.addMenu(theme_menu)
        toggle_service = QAction('Disable Service', self)
        quit_action = QAction('Quit', self)
        menu.addAction(toggle_service)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

        quit_action.triggered.connect(self.quit_app)
        self.activated.connect(self.on_activated)
        # Connect theme actions to save logic
        self.action_theme_light.triggered.connect(lambda: self.set_theme_pref('light'))
        self.action_theme_dark.triggered.connect(lambda: self.set_theme_pref('dark'))
        self.action_theme_auto.triggered.connect(lambda: self.set_theme_pref('auto'))
        self.action_theme_system.toggled.connect(self.set_system_color_pref)
        # Load preferences on startup
        self.load_theme_preferences()

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

    def set_theme_pref(self, theme):
        prefs = self.load_preferences()
        prefs['theme'] = theme
        self.save_preferences(prefs)
        self.action_theme_light.setChecked(theme == 'light')
        self.action_theme_dark.setChecked(theme == 'dark')
        self.action_theme_auto.setChecked(theme == 'auto')

    def set_system_color_pref(self, checked):
        prefs = self.load_preferences()
        prefs['use_system_color'] = checked
        self.save_preferences(prefs)
        self.action_theme_system.setChecked(checked)

    def load_theme_preferences(self):
        prefs = self.load_preferences()
        theme = prefs.get('theme', 'auto')
        use_system_color = prefs.get('use_system_color', False)
        self.action_theme_light.setChecked(theme == 'light')
        self.action_theme_dark.setChecked(theme == 'dark')
        self.action_theme_auto.setChecked(theme == 'auto')
        self.action_theme_system.setChecked(use_system_color)

    def load_preferences(self):
        try:
            with open(self.preferences_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_preferences(self, prefs):
        try:
            with open(self.preferences_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")
