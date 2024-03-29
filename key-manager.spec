# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from sys import platform

datas = []
if platform == "linux" or platform == "linux2":
    datas = [
      ('/usr/lib/x86_64-linux-gnu/libssl.so.3', '.'),
      ('/usr/lib/x86_64-linux-gnu/libcrypto.so.3', '.'),
      ('/usr/lib/x86_64-linux-gnu/libffi.so.8', '.')
    ]
datas += collect_data_files('key_manager')
datas += collect_data_files('eth_account')


block_cipher = None


a = Analysis(
    ['key_manager/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['multiaddr.codecs.uint16be', 'multiaddr.codecs.idna'],
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
    name='key-manager',
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
