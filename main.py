from PyQt6.QtWidgets import QApplication
import sys
import multiprocessing
import atexit
from floating_widget import FloatingWidget
from tray_icon import TrayIcon
import background_service

background_process = None
stop_queue = None

def run_background_service_process(queue):
    """The entry point for the background process."""
    service = background_service.BackgroundService(stop_queue=queue)
    service.run()

def run_background_service():
    global background_process, stop_queue
    stop_queue = multiprocessing.Queue()
    background_process = multiprocessing.Process(target=run_background_service_process, args=(stop_queue,))
    background_process.start()

def cleanup_background_process():
    if background_process and background_process.is_alive():
        print("Requesting background service to stop...")
        stop_queue.put('stop')
        background_process.join(timeout=10) # Wait for clean exit
        if background_process.is_alive():
            print("Background service did not stop gracefully, terminating.")
            background_process.terminate()
            background_process.join()
        else:
            print("Background service stopped gracefully.")

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