# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['D:\vsc\PQt\Qtic'],
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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
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
    console=False, # Set to True if you want a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
