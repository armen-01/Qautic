from PyQt6.QtWidgets import QApplication
import sys
import multiprocessing
import subprocess
import atexit
from floating_widget import FloatingWidget
from tray_icon import TrayIcon

background_process = None

def run_background_service():
    # Use subprocess to run the script in a new process
    global background_process
    background_process = subprocess.Popen([sys.executable, "background_service.py"])

def cleanup_background_process():
    if background_process:
        background_process.terminate()
        background_process.wait()

if __name__ == "__main__":
    multiprocessing.freeze_support()  # For PyInstaller
    
    run_background_service()
    atexit.register(cleanup_background_process)

    app = QApplication(sys.argv)
    screen = app.primaryScreen().availableGeometry()
    widget_width = 420
    widget_height = 750
    x = screen.width() - widget_width
    y = screen.height() - widget_height
    
    floating_widget = FloatingWidget(x + 1, y - 30, widget_width, widget_height)
    floating_widget.hide()

    tray = TrayIcon(floating_widget)
    tray.show()
    
    sys.exit(app.exec())
