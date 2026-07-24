# -*- mode: python ; coding: utf-8 -*-
"""
PI Manager AllInOne - PyInstaller onefile 打包配置

入口：backend/run_combined.py
包含：backend 全模块 + client 全模块 + frontend/dist（内置兜底）

打包后 _MEIPASS 结构：
  _MEIPASS/frontend_dist/  ← 内置前端兜底（永不更新）
  _MEIPASS/keys/           ← ECDSA 公钥（生产）
  exe 同级目录（用户可写）：
  ./dist/                   ← CDN 下载的可更新前端包
  ./data/                   ← SQLite 数据库
"""
import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
CLIENT_DIR = os.path.join(PROJECT_ROOT, 'client')
ENTRY_SCRIPT = os.path.join(BACKEND_DIR, 'run_combined.py')

# ---- hiddenimports ----
hiddenimports = []
hiddenimports += collect_submodules('app')

for sub in ('api', 'config', 'dialogs', 'services', 'utils', 'widgets', 'web_container'):
    hiddenimports += collect_submodules(sub)

hiddenimports += [
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    'PySide6.QtNetwork', 'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
    'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore',
    'PySide6.QtWebChannel',
    'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'PyQt5.QtNetwork', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebChannel',
    'pywebchannel', 'requests', 'openpyxl',
]

hiddenimports += [
    'app.migration_manager', 'frontend_manager', 'qt_bridge',
    'sqlalchemy', 'sqlalchemy.dialects.sqlite', 'sqlalchemy.dialects.mysql',
    'pymysql', 'cryptography', 'ecdsa', 'hashlib', 'urllib',
]

# ---- datas ----
datas = []

frontend_dist_src = os.path.join(PROJECT_ROOT, 'frontend', 'dist')
if os.path.isdir(frontend_dist_src):
    datas.append((frontend_dist_src, 'frontend_dist'))
else:
    print('[Spec] 警告: frontend/dist 未找到，跳过内置前端兜底，请先运行 npm run build')

keys_src = os.path.join(BACKEND_DIR, 'keys')
if os.path.isdir(keys_src):
    datas.append((keys_src, 'keys'))

a = Analysis(
    [ENTRY_SCRIPT],
    pathex=[BACKEND_DIR, CLIENT_DIR, PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas',
        'PyQt6', 'PyQt6.QtCore',
    ],
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
    name='PI-Manager-AllInOne',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PI-Manager-AllInOne',
)
