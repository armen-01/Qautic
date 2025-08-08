# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('Switch-NightLight.psm1', '.'),
    ],
    hiddenimports=[
        'PyQt6.sip',
        'psutil',
        'watchdog',
        'screen_brightness_control',
        'pycaw',
        'winsdk',
        'comtypes',
        'pywin32',
        'WMI',
        'json_handler',
        'floating_widget',
        'tray_icon',
        'background_service',
        'floating_widget_default_item',
        'floating_widget_menu_main',
        'floating_widget_painter',
        'settings_tile_functions',
        'ui_colors',
        'ui_sub_widgets.hide_button',
        'ui_sub_widgets.list_base',
        'ui_sub_widgets.program_item',
        'ui_sub_widgets.settings_tile',
        'ui_sub_widgets.splitter',
        'winaccent',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6.Qt3DCore',
        'PyQt6.Qt3DExtras',
        'PyQt6.Qt3DInput',
        'PyQt6.Qt3DLogic',
        'PyQt6.Qt3DRender',
        'PyQt6.QtBluetooth',
        'PyQt6.QtDataVisualization',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtLocation',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtNfc',
        'PyQt6.QtNetwork',
        'PyQt6.QtOpenGL',
        'PyQt6.QtPdf',
        'PyQt6.QtPositioning',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuick3D',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtRemoteObjects',
        'PyQt6.QtSensors',
        'PyQt6.QtSerialPort',
        'PyQt6.QtSql',
        'PyQt6.QtSvg',
        'PyQt6.QtTest',
        'PyQt6.QtTextToSpeech',
        'PyQt6.QtWebChannel',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebSockets',
        'PyQt6.QtXml',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# --- Direct filtering of bundled files ---
print("--- Filtering collected data files ---")
original_data_count = len(a.datas)

# Define a function to decide which files to keep
def is_data_to_keep(dest_path):
    # Exclude all translation files
    if 'PyQt6/Qt6/translations' in dest_path:
        return False
    # Exclude most plugins, keeping only essential ones
    if 'PyQt6/Qt6/plugins' in dest_path:
        if 'platforms' in dest_path or 'styles' in dest_path or 'iconengines' in dest_path:
            return True  # Keep these essential plugins
        return False # Exclude all other plugins
    return True # Keep everything else

# Apply the filter to the list of data files
a.datas = [data for data in a.datas if is_data_to_keep(data[0].replace(os.sep, '/'))]

print(f"--- Filtering complete. Removed {original_data_count - len(a.datas)} data files. ---")
# --- End of filtering ---

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Qautic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    icon='assets\graphics\ico.png',
    console=False, # Set to True if you want a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)