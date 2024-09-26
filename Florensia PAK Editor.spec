# -*- mode: python ; coding: utf-8 -*-
import tomllib

with open("pyproject.toml", "r") as fp:
    toml = tomllib.loads(fp.read())
    version = toml["tool"]["poetry"]["version"]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ("./pak_editor/assets", ".")
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'Florensia PAK Editor v{version}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['pak_editor\\assets\\icon.ico'],
)
