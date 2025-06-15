# SagaAppLauncher.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('icons/mayaIcon.png', 'icons'),
    ('icons/unrealIcon.png', 'icons'),
    ('icons/appIcon.ico', 'icons'),
    ('icons/dropDownArrow.png', 'icons'),
    ('icons/aeIcon.png', 'icons'),
    ('styles/dark.qss', 'styles'),
    ('batchFiles/launchMaya.bat', 'batch_files'),
    ('batchFiles/launchUnrealProject.bat', 'batch_files'),
    ('C:/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.10_3.10.3056.0_x64__qbz5n2kfra8p0/python310.dll', '.')
]

a = Analysis(
    ['SagaAppLauncher.py'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SagaAppLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icons/appIcon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SagaAppLauncher',
)
