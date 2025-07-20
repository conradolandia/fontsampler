# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['fontsampler.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'fontTools.ttLib',
        'reportlab.pdfgen',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'PyPDF2',
        'PIL',
        'PIL._imaging',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy'],  # Exclude unused heavy dependencies
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