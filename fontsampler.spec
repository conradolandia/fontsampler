# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs

# Collect Cairo libraries
cairo_libs = collect_dynamic_libs('cairocffi')

a = Analysis(
    ['fontsampler.py'],
    pathex=[],
    binaries=cairo_libs,
    datas=[],
    hiddenimports=[
        'fontTools.ttLib',
        'fontTools.ttLib.ttFont',
        'fontTools.ttLib.tables',
        'fontTools.ttLib.tables._n_a_m_e',
        'weasyprint',
        'weasyprint.text.fonts',
        'weasyprint.css',
        'weasyprint.css.targets',
        'weasyprint.document',
        'weasyprint.html',
        'weasyprint.layout',
        'weasyprint.pdf',
        'cairocffi',
        'cairocffi.pixbuf',
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='fontsampler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
