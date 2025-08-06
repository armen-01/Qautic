from PyQt6.QtWidgets import QApplication
import sys
import multiprocessing
import atexit
from floating_widget import FloatingWidget
from tray_icon import TrayIcon
import background_service

background_process = None

def run_background_service_process():
    service = background_service.BackgroundService()
    service.run()

def run_background_service():
    global background_process
    background_process = multiprocessing.Process(target=run_background_service_process)
    background_process.start()

def cleanup_background_process():
    if background_process and background_process.is_alive():
        background_process.terminate()
        background_process.join()

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
