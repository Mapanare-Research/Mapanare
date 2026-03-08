# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

is_windows = sys.platform == 'win32'
is_macos = sys.platform == 'darwin'

# Strip debug symbols on Linux/macOS
do_strip = not is_windows
# Disable UPX on Windows (causes antivirus false positives)
do_upx = not is_windows

# Collect all mapa submodules (parser, semantic, emit, jit, lsp, etc.)
mapa_submodules = collect_submodules('mapa')
runtime_submodules = collect_submodules('runtime')
stdlib_submodules = collect_submodules('stdlib')

# Copy metadata so importlib.metadata works
mapa_metadata = copy_metadata('mapanare')

sep = os.sep

a = Analysis(
    [f'pyinstaller-entry.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('mapa', 'mapa'),
        ('runtime', 'runtime'),
        ('stdlib', 'stdlib'),
        ('VERSION', '.'),
    ] + mapa_metadata,
    hiddenimports=[
        'lark',
        'llvmlite',
        'llvmlite.binding',
    ] + mapa_submodules + runtime_submodules + stdlib_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # LSP deps (not needed in standalone CLI)
        'pygls',
        'lsprotocol',
        # Dev tools
        'pytest',
        '_pytest',
        'mypy',
        'black',
        'ruff',
        # Heavy deps not needed at runtime
        'setuptools',
        'pip',
        'fontTools',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mapa',
    debug=False,
    bootloader_ignore_signals=False,
    strip=do_strip,
    upx=do_upx,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64' if is_macos else None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=do_strip,
    upx=do_upx,
    upx_exclude=[],
    name='mapa',
)
