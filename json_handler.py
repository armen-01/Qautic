import os
import json
import sys

def get_asset_path():
    """
    Gets the path to bundled assets (read-only).
    For a PyInstaller one-file bundle, this is the temporary _MEIPASS directory.
    For a one-folder bundle or running from source, it's the application's base directory.
    """
    if getattr(sys, 'frozen', False):
        # The application is frozen (e.g., by PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            # This is a one-file bundle, assets are in the temporary directory
            return sys._MEIPASS
        else:
            # This is a one-folder bundle, assets are in the executable's directory
            return os.path.dirname(sys.executable)
    else:
        # The application is running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

def get_data_path():
    """
    Gets the path for writable data files (e.g., config).
    This is always a persistent, writable location.
    For a bundled app, this is the directory of the executable.
    For running from source, it's the application's base directory.
    """
    if getattr(sys, 'frozen', False):
        # For any PyInstaller bundle, use the directory of the executable
        return os.path.dirname(sys.executable)
    else:
        # The application is running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

def get_preferences_path():
    return os.path.join(get_data_path(), 'preferences.json')

def get_programs_path():
    return os.path.join(get_data_path(), 'programs.json')

def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving to {os.path.basename(path)}: {e}")

def load_preferences():
    return load_json(get_preferences_path(), {})

def save_preferences(prefs):
    save_json(get_preferences_path(), prefs)

def load_programs():
    return load_json(get_programs_path(), [])

def save_programs(programs):
    save_json(get_programs_path(), programs)