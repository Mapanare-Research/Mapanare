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

# Collect all mapanare submodules (parser, semantic, emit, jit, lsp, etc.)
mapanare_submodules = collect_submodules('mapanare')
runtime_submodules = collect_submodules('runtime')
stdlib_submodules = collect_submodules('stdlib')

# Copy metadata so importlib.metadata works
mapanare_metadata = copy_metadata('mapanare')

sep = os.sep

# Paths are relative to this spec file; go up one level to reach repo root
root = os.path.normpath(os.path.join(SPECPATH, '..'))

# Optionally stage a portable C toolchain next to the exe. This is populated
# by the publish.yml Windows job (w64devkit x64) before calling PyInstaller.
# If the directory exists, ship it; otherwise the bundle relies on a system
# gcc/clang being on PATH (consistent with Linux / macOS behavior).
bundled_datas = [
    (os.path.join(root, 'mapanare'), 'mapanare'),
    (os.path.join(root, 'runtime'), 'runtime'),
    (os.path.join(root, 'stdlib'), 'stdlib'),
    (os.path.join(root, 'VERSION'), '.'),
]

toolchain_dir = os.path.join(root, 'toolchain')
if os.path.isdir(toolchain_dir):
    bundled_datas.append((toolchain_dir, 'toolchain'))

a = Analysis(
    [os.path.join(root, 'packaging', 'pyinstaller-entry.py')],
    pathex=[root],
    binaries=[],
    datas=bundled_datas + mapanare_metadata,
    hiddenimports=[
        'lark',
        'llvmlite',
        'llvmlite.binding',
    ] + mapanare_submodules + runtime_submodules + stdlib_submodules,
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

icon_path = os.path.join(root, 'packaging', 'mapanare.ico') if is_windows else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mapanare',
    debug=False,
    bootloader_ignore_signals=False,
    strip=do_strip,
    upx=do_upx,
    upx_exclude=[],
    icon=icon_path,
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
    name='mapanare',
)
