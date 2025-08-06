import os
import subprocess
import winreg
import ctypes
import sys
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CoInitialize, CoUninitialize, CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from winsdk.windows.devices.radios import Radio, RadioKind, RadioState
from winsdk.windows.networking.networkoperators import NetworkOperatorTetheringManager
from winsdk.windows.networking.connectivity import NetworkInformation
import win32com.client

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

    def set_microphone(self, state):
        if state.get('is_unchanged', True): return
        CoInitialize()
        try:
            mic = AudioUtilities.GetMicrophone()
            interface = mic.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            is_muted = state.get('tile_value') == 1
            volume.SetMute(is_muted, None)
        except Exception as e:
            print(f"Error setting microphone mute: {e}")
        finally:
            CoUninitialize()

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
        self.set_microphone(settings_profile.get('microphone', {'is_unchanged': True}))
        self.set_startup(settings_profile.get('startup', {'is_unchanged': True}), program_path, profile_name)
