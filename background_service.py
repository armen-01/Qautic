import os
import time
import threading
import asyncio
import wmi
import pythoncom

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from json_handler import load_preferences, load_programs, get_preferences_path, get_programs_path
from settings_tile_functions import SettingsManager

class AsyncRunner:
    """Provides a separate thread for running asyncio event loops."""
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_coroutine(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

class JsonFileHandler(FileSystemEventHandler):
    """Responds to changes in the JSON configuration files."""
    def __init__(self, service):
        self.service = service

    def on_modified(self, event):
        if not event.is_directory:
            time.sleep(0.1) # Wait for write to complete
            if event.src_path == get_preferences_path():
                self.service.on_preferences_changed()
            elif event.src_path == get_programs_path():
                self.service.on_programs_changed()

class BackgroundService:
    """
    Monitors running processes and applies system settings based on user-defined profiles.
    This service is event-driven, using WMI for efficient, real-time process monitoring.
    """
    def __init__(self):
        self.async_runner = AsyncRunner()
        self.settings_manager = SettingsManager(self.async_runner)
        
        # --- State Management ---
        self.running_apps_stack = []
        self.monitored_programs = []
        self.monitored_executables = {}
        self.service_enabled = True
        self.default_settings_option = 'use'
        self.last_applied_profile_name = None
        
        # --- Threading and Events ---
        self.lock = threading.Lock()
        self.wmi_thread = None
        self.stop_event = threading.Event()
        self.rescan_needed = threading.Event()

    def run(self):
        """Starts the background service and all its components."""
        self._load_initial_state()
        self._setup_watchers()
        
        self.wmi_thread = threading.Thread(target=self._wmi_event_loop, daemon=True)
        self.wmi_thread.start()

        print("Background service is running. Press Ctrl+C to stop.")
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stops the service and cleans up resources."""
        print("Stopping background service...")
        self.stop_event.set()
        if self.wmi_thread:
            self.wmi_thread.join()
        self.async_runner.loop.call_soon_threadsafe(self.async_runner.loop.stop)
        print("Service stopped.")

    def _load_initial_state(self):
        """Loads all preferences and triggers the first process scan."""
        print("Loading initial state...")
        self.on_preferences_changed()
        self.on_programs_changed() # This also flags for the initial scan

    def _setup_watchers(self):
        """Sets up watchdog to monitor JSON configuration files for changes."""
        event_handler = JsonFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(get_preferences_path()), recursive=False)
        observer.start()

    def on_preferences_changed(self):
        """Handles changes to 'preferences.json'."""
        with self.lock:
            prefs = load_preferences()
            self.service_enabled = prefs.get('service_enabled', True)
            self.default_settings_option = prefs.get('default_settings_option', 'use')
        print(f"Preferences updated: Service Enabled={self.service_enabled}, Default Option='{self.default_settings_option}'")
        self.update_settings()

    def on_programs_changed(self):
        """Handles changes to 'programs.json' and flags for a rescan."""
        with self.lock:
            self.monitored_programs = load_programs()
            self.monitored_executables = {
                os.path.basename(prog['path']).lower(): prog 
                for prog in self.monitored_programs if prog.get('is_enabled', True)
            }
        print(f"Monitored programs list updated. Flagging for rescan.")
        self.rescan_needed.set()

    def _perform_process_scan(self):
        """
        Scans for running monitored processes using a targeted WQL query.
        This is the single source of truth for the running application stack.
        MUST be called from the WMI thread.
        """
        print("Performing targeted process scan...")
        
        with self.lock:
            monitored_names = list(self.monitored_executables.keys())
            if not monitored_names:
                self.running_apps_stack = []
            else:
                # Build a WQL query for efficiency
                where_clause = " OR ".join([f"Name = '{name}'" for name in monitored_names])
                query = f"SELECT ProcessId, Name FROM Win32_Process WHERE {where_clause}"
                
                c = wmi.WMI()
                found_processes = c.query(query)

                new_stack = []
                for process in found_processes:
                    try:
                        p_name = process.Name.lower()
                        if p_name in self.monitored_executables:
                            prog_data = self.monitored_executables[p_name]
                            new_stack.append({
                                'name': prog_data['name'],
                                'pid': process.ProcessId,
                                'settings': prog_data['settings'],
                                'path': prog_data['path']
                            })
                    except Exception:
                        continue
                
                self.running_apps_stack = new_stack
                self.sort_stack()
        
        self.update_settings()

    def _wmi_event_loop(self):
        """
        The core event-driven loop. It watches for any process change and
        triggers a full, reliable rescan.
        """
        pythoncom.CoInitialize()
        try:
            raw_wql = "SELECT * FROM __InstanceOperationEvent WITHIN 2 WHERE TargetInstance ISA 'Win32_Process'"
            c = wmi.WMI()
            watcher = c.watch_for(raw_wql=raw_wql)
            print("WMI event watcher started.")

            while not self.stop_event.is_set():
                # Always check for a manual rescan request first
                if self.rescan_needed.is_set():
                    self.rescan_needed.clear()
                    self._perform_process_scan()

                try:
                    # Wait for any process creation or deletion event
                    event = watcher(timeout_ms=1000)
                    if event:
                        # An event occurred, so the list of running processes may have changed.
                        # Trigger a rescan to ensure the state is 100% accurate.
                        print("WMI event detected, triggering a rescan.")
                        self._perform_process_scan()
                except wmi.x_wmi_timed_out:
                    continue # This is normal, just means no events happened
                except Exception as e:
                    print(f"[ERROR] An unexpected error occurred in WMI loop: {e}")
                    time.sleep(2) # Prevent rapid-fire errors
        finally:
            pythoncom.CoUninitialize()
            print("WMI event watcher stopped.")

    def sort_stack(self):
        """
        Sorts the running apps stack by priority.
        """
        self.running_apps_stack.sort(key=lambda x: (
            x['settings'].get('priority', {}).get('is_unchanged', True),
            x['settings'].get('priority', {}).get('tile_value', 9999)
        ))
        # Debug print for the queue state
        stack_names = [app['name'] for app in self.running_apps_stack]
        print(f"[QUEUE] Priority stack updated: {stack_names}")

    def update_settings(self):
        """
        The core state machine. Determines the correct profile and applies it
        ONLY if it's different from the last applied profile.
        """
        with self.lock:
            target_profile_name = None
            target_profile_settings = None
            target_profile_path = None

            if not self.service_enabled:
                target_profile_name = "service_disabled"
            elif self.running_apps_stack:
                top_app = self.running_apps_stack[0]
                target_profile_name = top_app['name']
                target_profile_settings = top_app['settings']
                target_profile_path = top_app['path']
            else:
                if self.default_settings_option == 'use':
                    prefs = load_preferences()
                    target_profile_name = "Default"
                    target_profile_settings = prefs.get('default_settings', {})
                    target_profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
                else:
                    target_profile_name = "Idle"

            if target_profile_name != self.last_applied_profile_name:
                print(f"State change: '{self.last_applied_profile_name}' -> '{target_profile_name}'")
                if target_profile_settings:
                    self.settings_manager.apply_settings(target_profile_settings, target_profile_name, target_profile_path)
                self.last_applied_profile_name = target_profile_name

if __name__ == '__main__':
    service = BackgroundService()
    service.run()
