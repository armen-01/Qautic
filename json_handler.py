import os
import json

def _get_base_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_preferences_path():
    return os.path.join(_get_base_dir(), 'preferences.json')

def get_programs_path():
    return os.path.join(_get_base_dir(), 'programs.json')

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
