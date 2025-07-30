import os
import time
import psutil
import threading
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from json_handler import load_preferences, load_programs, get_preferences_path, get_programs_path
from settings_tile_functions import SettingsManager

class AsyncRunner:
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
    def __init__(self, service):
        self.service = service

    def on_modified(self, event):
        if not event.is_directory:
            time.sleep(0.1)
            if event.src_path == get_preferences_path():
                self.service.on_preferences_changed()
            elif event.src_path == get_programs_path():
                self.service.on_programs_changed()

class BackgroundService:
    def __init__(self):
        self.async_runner = AsyncRunner()
        self.settings_manager = SettingsManager(self.async_runner)
        self.running_apps_stack = []
        self.service_enabled = False
        self.default_settings_option = 'use'
        #self.fallback_settings = {}
        self.monitored_programs = []
        self.lock = threading.Lock()
        self.last_applied_profile_name = None

    def run(self):
        self._load_initial_state()
        self._setup_watchers()
        process_monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        process_monitor_thread.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.async_runner.loop.call_soon_threadsafe(self.async_runner.loop.stop)

    def _load_initial_state(self):
        self.on_preferences_changed()
        self.on_programs_changed()

    def _setup_watchers(self):
        event_handler = JsonFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(get_preferences_path()), recursive=False)
        observer.start()

    def on_preferences_changed(self):
        with self.lock:
            prefs = load_preferences()
            self.service_enabled = prefs.get('service_enabled', True)
            self.default_settings_option = prefs.get('default_settings_option', 'use')
        self.update_settings()

    def on_programs_changed(self):
        with self.lock:
            self.monitored_programs = load_programs()
        self.update_running_apps_stack()

    def monitor_processes(self):
        while True:
            self.update_running_apps_stack()
            time.sleep(2)

    def update_running_apps_stack(self):
        with self.lock:
            running_pids = {p.pid for p in psutil.process_iter(['pid'])}
            current_stack_pids = {app['pid'] for app in self.running_apps_stack}
            
            for prog in self.monitored_programs:
                if not prog.get('is_enabled', True):
                    continue
                prog_exe_name = os.path.basename(prog['path']).lower()
                try:
                    for p in psutil.process_iter(['pid', 'name']):
                        if p.info['name'].lower() == prog_exe_name and p.info['pid'] not in current_stack_pids:
                            self.running_apps_stack.append({'name': prog['name'], 'pid': p.info['pid'], 'settings': prog['settings'], 'path': prog['path']})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            self.running_apps_stack = [app for app in self.running_apps_stack if app['pid'] in running_pids]
            self.sort_stack()
        self.update_settings()

    def sort_stack(self):
        self.running_apps_stack.sort(key=lambda x: (x['settings'].get('priority', {}).get('is_unchanged', True), x['settings'].get('priority', {}).get('tile_value', 9999)))

    def update_settings(self):
        with self.lock:
            if not self.service_enabled:
                if self.last_applied_profile_name != "service_disabled":
                    self.last_applied_profile_name = "service_disabled"
                return

            profile_to_apply = None
            profile_name = "none"
            program_path = None

            if self.running_apps_stack:
                top_app = self.running_apps_stack[0]
                profile_to_apply = top_app['settings']
                profile_name = top_app['name']
                program_path = top_app['path']
            else:
                if self.default_settings_option == 'use':
                    prefs = load_preferences()
                    profile_to_apply = prefs.get('default_settings', {})
                    profile_name = "Default (use)"
                    program_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
                # elif self.default_settings_option == 'fallback':
                #     profile_to_apply = self.fallback_settings
                #     profile_name = "Default (fallback)"
                else:
                    profile_name = "Default (disabled)"

            if profile_name != self.last_applied_profile_name:
                self.settings_manager.apply_settings(profile_to_apply, profile_name, program_path)
                self.last_applied_profile_name = profile_name

if __name__ == '__main__':
    service = BackgroundService()
    service.run()