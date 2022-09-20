# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['mlox/__main__.py'],
             pathex=['mlox'],
             binaries=[],
             datas=[
                 ('mlox/static/', 'mlox/static'),  # For static files
                 (HOMEPATH + '\\PyQt5\\Qt5\\bin\\*', 'PyQt5\\Qt5\\bin')  # Fixes a bug with Qt
             ],
             hiddenimports=['mlox.static', 'libarchive', 'appdirs', 'PyQt5'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          # exclude_binaries=True,
          name='mlox',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True , icon='mlox\\static\\mlox.ico')
# coll = COLLECT(exe,
#                a.binaries,
#                a.zipfiles,
#                a.datas,
#                strip=False,
#                upx=True,
#                upx_exclude=[],
#                name='mlox')
