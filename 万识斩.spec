# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_data_files
import sys
import os

datas = [('client\\resource', 'client\\resource')]
binaries = []
hiddenimports = [
    'py_opengauss',
    'py_opengauss.dbapi',
    'py_opengauss.driver',
    'qfluentwidgets',
    'qframelesswindow',
    'openai',
    'pandas',
    'openpyxl',
    'server.db_config',
    'server.database_manager',
    'server.my_test',
    'client.data_view',
    'client.AI',
    'markdown'
]

# 收集 py_opengauss 的所有数据文件和动态库
try:
    tmp_ret = collect_all('py_opengauss')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception as e:
    print(f"Warning: Could not collect py_opengauss: {e}")

# 收集 qfluentwidgets
tmp_ret = collect_all('qfluentwidgets')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


a = Analysis(
    ['client\\main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='万识斩',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 关闭控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['client\\resource\\logo.png'],
)
