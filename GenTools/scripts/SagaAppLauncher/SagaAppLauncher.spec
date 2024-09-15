# saga_launcher.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('icons/mayaIcon.png', 'icons'),
    ('icons/unrealIcon.png', 'icons'),
    ('styles/dark.qss', 'styles'),
    ('batch_files/launchMaya2023.bat', 'batch_files'),
    ('batch_files/launchUnrealProject.bat', 'batch_files'),
]

a = Analysis(
    ['saga_launcher.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='saga_launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,  # Replace with 'your_icon.ico' if you have an application icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='saga_launcher',
)
