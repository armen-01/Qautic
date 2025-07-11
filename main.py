from PyQt6.QtWidgets import QApplication
import sys
from floating_widget import FloatingWidget
from tray_icon import TrayIcon

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create the floating widget (hidden by default)
    screen = app.primaryScreen().availableGeometry()
    widget_width = 420
    widget_height = 750
    x = screen.width() - widget_width
    y = screen.height() - widget_height
    floating_widget = FloatingWidget(x + 1, y - 30, widget_width, widget_height)
    floating_widget.hide()
    # Create the tray icon and pass the floating widget to it
    tray = TrayIcon(floating_widget)
    tray.show()
    sys.exit(app.exec())