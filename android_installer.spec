# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:\\GitHub\\android_installer\\src\\main.py'],
    pathex=['E:\\GitHub\\android_installer\\src'],
    binaries=[],
    datas=[],
    hiddenimports=['win32gui', 'win32con'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='android_installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:\\Users\\ADMINI~1\\AppData\\Local\\Temp\\tmpjz0kncdd.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='android_installer',
)
