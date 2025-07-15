from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle, QDialog, QVBoxLayout, QLabel, QSlider, QPushButton
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, Qt
from ui_sub_widgets.list_base import ListBase

class SliderDialog(QDialog):
    value_changed = pyqtSignal(int)

    def __init__(self, value=100, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Adjust Value')
        self.setFixedWidth(250)
        layout = QVBoxLayout(self)
        self.label = QLabel(f"Value: {value}", self)
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(200)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        btn = QPushButton('OK', self)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def _on_value_changed(self, val):
        self.label.setText(f"Value: {val}")
        self.value_changed.emit(val)

class TrayIcon(QSystemTrayIcon):
    def __init__(self, floating_widget, parent=None):
        super().__init__(parent)
        self.floating_widget = floating_widget
        self.slider_value = 74

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
        show_action = QAction('Show', self)
        hide_action = QAction('Hide', self)
        toggle_service = QAction('Disable', self)
        slider_action = QAction('Adjust Value...', self)
        quit_action = QAction('Quit', self)
        menu.addAction(show_action)
        menu.addAction(hide_action)
        menu.addAction(slider_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

        show_action.triggered.connect(self.show_widget)
        hide_action.triggered.connect(self.hide_widget)
        slider_action.triggered.connect(self.show_slider_dialog)
        quit_action.triggered.connect(self.quit_app)

        self.activated.connect(self.on_activated)

    def show_widget(self):
        self.floating_widget.slide_in()

    def hide_widget(self):
        self.floating_widget.slide_out()

    def show_slider_dialog(self):
        dlg = SliderDialog(self.slider_value, parent=self.floating_widget)
        dlg.value_changed.connect(self.set_slider_value)
        if dlg.exec():
            self.set_slider_value(dlg.slider.value())

    def set_slider_value(self, value):
        self.slider_value = value
        ListBase.update_grid_size(value)

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
