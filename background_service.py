import os
import time
import subprocess
import psutil
import threading
import asyncio
import winreg
import ctypes
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from json_handler import load_preferences, load_programs, get_preferences_path, get_programs_path
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CoInitialize, CoUninitialize, CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from winsdk.windows.devices.radios import Radio, RadioKind, RadioState
from winsdk.windows.networking.networkoperators import NetworkOperatorTetheringManager
from winsdk.windows.networking.connectivity import NetworkInformation
import win32com.client

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

class SettingsManager:
    def __init__(self, async_runner):
        self.async_runner = async_runner

    def _run_powershell(self, command):
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error executing PowerShell command: {e}")
            print(f"Stderr: {e.stderr}")
            print(f"Stdout: {e.stdout}")
        except Exception as e:
            print(f"An unexpected error occurred while executing PowerShell command: {e}")

    async def _set_radio_state_async(self, kind, turn_on):
        try:
            all_radios = await Radio.get_radios_async()
            for r in all_radios:
                if r.kind == kind:
                    await r.set_state_async(RadioState.ON if turn_on else RadioState.OFF)
        except Exception as e:
            print(f"Error setting radio state for {kind.name}: {e}")

    def _set_radio_state(self, kind, turn_on):
        self.async_runner.run_coroutine(self._set_radio_state_async(kind, turn_on))

    async def _set_hotspot_state_async(self, turn_on):
        try:
            connection_profile = NetworkInformation.get_internet_connection_profile()
            if not connection_profile:
                print("Error: Not connected to a network. Cannot manage hotspot.")
                return
            tethering_manager = NetworkOperatorTetheringManager.create_from_connection_profile(connection_profile)
            if turn_on:
                await tethering_manager.start_tethering_async()
            else:
                await tethering_manager.stop_tethering_async()
        except Exception as e:
            print(f"Error setting hotspot state: {e}")

    def set_hotspot(self, state):
        if state.get('is_unchanged', True): return
        self.async_runner.run_coroutine(self._set_hotspot_state_async(state.get('tile_value') == 0))

    def set_wifi(self, state):
        if state.get('is_unchanged', True): return
        self._set_radio_state(RadioKind.WI_FI, state.get('tile_value') == 0)

    def set_bluetooth(self, state):
        if state.get('is_unchanged', True): return
        self._set_radio_state(RadioKind.BLUETOOTH, state.get('tile_value') == 0)

    def set_airplane_mode(self, state):
        if state.get('is_unchanged', True): return
        
        # UI "On" (tile_value 0) -> Airplane Mode ON -> PowerShell state 0
        # UI "Off" (tile_value 1) -> Airplane Mode OFF -> PowerShell state 1
        turn_on = state.get('tile_value') == 0
        desired_state = 0 if turn_on else 1

        command = f"""
        Add-Type -TypeDefinition @'
        using System;
        using System.Runtime.InteropServices;

        public static class NativeMethods {{
            [DllImport("ole32.dll")]
            public static extern int CoInitialize(IntPtr pv);
            [DllImport("ole32.dll")]
            public static extern void CoUninitialize();
            [DllImport("ole32.dll")]
            public static extern uint CoCreateInstance(Guid clsid, IntPtr pv, uint ctx, Guid iid, out IntPtr ppv);
        }}

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate int GetSystemRadioStateDelegate(IntPtr cg, out int ie, out int se, out int p3);

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate int SetSystemRadioStateDelegate(IntPtr ptr, int state);

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        public delegate int ReleaseDelegate(IntPtr ptr);
'@

        $CLSID = '581333F6-28DB-41BE-BC7A-FF201F12F3F6'
        $IID   = 'DB3AFBFB-08E6-46C6-AA70-BF9A34C30AB7'
        $mrs   = [System.Runtime.InteropServices.Marshal]
        $desiredState = {desired_state}

        try {{
            $irm  = 0
            $null = [NativeMethods]::CoInitialize(0)
            $null = [NativeMethods]::CoCreateInstance($CLSID, 0, 4, $IID, [ref]$irm)

            $comPtr  = $mrs::ReadIntPtr($irm)
            $methodPtr  = [IntPtr[]]::new(8)
            $mrs::Copy($comPtr, $methodPtr, 0, $methodPtr.Length)

            $getState = $mrs::GetDelegateForFunctionPointer($methodPtr[5], [GetSystemRadioStateDelegate])
            $setState = $mrs::GetDelegateForFunctionPointer($methodPtr[6], [SetSystemRadioStateDelegate])
            $release  = $mrs::GetDelegateForFunctionPointer($methodPtr[2], [ReleaseDelegate])

            $currentState, $p2, $p3 = (0,0,0)
            $null = $getState.Invoke($irm, [ref]$currentState, [ref]$p2, [ref]$p3)

            if ($currentState -ne $desiredState) {{
                $null = $setState.Invoke($irm, $desiredState)
            }}
            
            $null = $release.Invoke($irm)
        }}
        finally {{
            $null = [NativeMethods]::CoUninitialize()
        }}
        """
        try:
            self._run_powershell(command)
        except Exception as e:
            print(f"Error setting airplane mode: {e}")

    def set_brightness(self, state):
        if state.get('is_unchanged', True): return
        try:
            sbc.set_brightness(state.get('tile_value', 100))
        except Exception as e:
            print(f"Error setting brightness: {e}")

    def set_volume(self, state):
        if state.get('is_unchanged', True): return
        CoInitialize()
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            level = state.get('tile_value', 100)
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        finally:
            CoUninitialize()

    def set_performance_mode(self, state):
        if state.get('is_unchanged', True): return
        power_schemes = {0: "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", 1: "381b4222-f694-41f0-9685-ff5bb260df2e", 2: "a1841308-3541-4fab-bc81-f71556f20b4a"}
        scheme_guid = power_schemes.get(state.get('tile_value'))
        if scheme_guid:
            self._run_powershell(f"powercfg /setactive {scheme_guid}")

    def set_system_color(self, state):
        if state.get('is_unchanged', True): return
        new_value = 1 - state.get('tile_value', 0)
        self._run_powershell(f"Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize' -Name AppsUseLightTheme -Value {new_value}")

    def set_night_light(self, state):
        if state.get('is_unchanged', True): return
        try:
            turn_on = state.get('tile_value') == 0
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Switch-NightLight.psm1')
            
            # The functions in the module are idempotent, so we can call them directly.
            action = "Enable-NightLight" if turn_on else "Disable-NightLight"
            
            # Import the module and call the appropriate function.
            command = f"Import-Module '{script_path}'; {action}"
            
            self._run_powershell(command)
        except Exception as e:
            print(f"Error setting night light: {e}")

    def set_notifications(self, state):
        if state.get('is_unchanged', True): return
        # UI "On" (tile_value 0) maps to "Priority Only" (Registry value 1)
        # UI "Off" (tile_value 1) maps to "Off" (Registry value 0)
        reg_level = 1 if state.get('tile_value', 1) == 0 else 0
        key_path = r'Software\Microsoft\Windows\CurrentVersion\FocusAssist'
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, 'Level', 0, winreg.REG_DWORD, reg_level)
            
            # Broadcast a specific WM_SETTINGCHANGE message for the registry key
            # This is often more reliable than a generic "Policy" broadcast.
            ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, key_path, 2, 1000, None)
        except Exception as e:
            print(f"Error setting notifications: {e}")

    def set_startup(self, state, program_path, program_name):
        if state.get('is_unchanged', True) or not program_path: return
        
        CoInitialize()
        try:
            turn_on = state.get('tile_value') == 0
            startup_folder = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
            shortcut_path = os.path.join(startup_folder, f"{program_name}.lnk")

            if turn_on:
                if not os.path.exists(shortcut_path):
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(shortcut_path)
                    if program_path.endswith('.py'):
                        python_exe_path = sys.executable
                        pythonw_exe_path = python_exe_path.replace("python.exe", "pythonw.exe")
                        shortcut.TargetPath = pythonw_exe_path
                        shortcut.Arguments = f'"{os.path.abspath(program_path)}"'
                    else:
                        shortcut.TargetPath = program_path
                    shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(program_path))
                    shortcut.save()
            else:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
        except Exception as e:
            print(f"Error managing startup shortcut: {e}")
        finally:
            CoUninitialize()


    def apply_settings(self, settings_profile, profile_name="Unknown", program_path=None):
        if not settings_profile: return
        
        airplane_state = settings_profile.get('airplane', {'is_unchanged': True})

        # Check if airplane mode is explicitly being turned ON by the profile
        is_airplane_on = not airplane_state.get('is_unchanged', True) and airplane_state.get('tile_value') == 0

        if is_airplane_on:
            self.set_airplane_mode(airplane_state)
        else:
            # If airplane mode is not being turned ON, it's either OFF or UNCHANGED.
            
            # Check if any other radio is being turned ON
            wifi_on = not settings_profile.get('wifi', {}).get('is_unchanged', True) and settings_profile.get('wifi', {}).get('tile_value') == 0
            bt_on = not settings_profile.get('bt', {}).get('is_unchanged', True) and settings_profile.get('bt', {}).get('tile_value') == 0
            hotspot_on = not settings_profile.get('hotspot', {}).get('is_unchanged', True) and settings_profile.get('hotspot', {}).get('tile_value') == 0

            # If airplane mode is explicitly set to OFF, or if any other radio is being turned ON,
            # we must first ensure airplane mode is OFF.
            is_airplane_off = not airplane_state.get('is_unchanged', True) and airplane_state.get('tile_value') == 1
            
            if is_airplane_off or wifi_on or bt_on or hotspot_on:
                self.set_airplane_mode({'tile_value': 1, 'is_unchanged': False}) # Force airplane mode OFF

            # Now apply the individual radio settings
            self.set_wifi(settings_profile.get('wifi', {'is_unchanged': True}))
            self.set_bluetooth(settings_profile.get('bt', {'is_unchanged': True}))
            self.set_hotspot(settings_profile.get('hotspot', {'is_unchanged': True}))

        self.set_brightness(settings_profile.get('brightness', {'is_unchanged': True}))
        self.set_volume(settings_profile.get('volume', {'is_unchanged': True}))
        self.set_performance_mode(settings_profile.get('performance', {'is_unchanged': True}))
        self.set_system_color(settings_profile.get('systemcolor', {'is_unchanged': True}))
        self.set_night_light(settings_profile.get('nightlight', {'is_unchanged': True}))
        self.set_notifications(settings_profile.get('notifications', {'is_unchanged': True}))
        self.set_startup(settings_profile.get('startup', {'is_unchanged': True}), program_path, profile_name)

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