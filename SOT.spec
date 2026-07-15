# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_all

datas = [
    ('firebase_key.json', '.'),
    ('ui/workspace.jpg', 'ui'),
    ('ui/logo.PNG',       'ui'),
    ('ui/logo.ico',       'ui'),
    ('assets/fonts/Inter-Regular.ttf',  'assets/fonts'),
    ('assets/fonts/Inter-Medium.ttf',   'assets/fonts'),
    ('assets/fonts/Inter-SemiBold.ttf', 'assets/fonts'),
    ('assets/fonts/Inter-Bold.ttf',     'assets/fonts'),
]
binaries = []
hiddenimports = ['firebase_admin', 'firebase_admin.credentials', 'firebase_admin.db', 'firebase_admin._http_client', 'google.cloud', 'google.auth', 'google.oauth2', 'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'openpyxl', 'openpyxl.styles', 'requests', 'pandas', 'core', 'core.auth', 'core.drawings', 'core.notes', 'core.projects', 'core.reports', 'core.users', 'services', 'services.firebase_client', 'services.auth_client', 'services.employee_performance_report', 'services.performance_report', 'services.project_report', 'services.project_status_report', 'ui', 'ui.main_window', 'ui.login_view', 'ui.admin_dashboard', 'ui.employee_dashboard', 'ui.admin_projects', 'ui.admin_review', 'ui.admin_template', 'ui.admin_tasks', 'ui.drawing_detail', 'ui.superadmin_users', 'utils', 'utils.logger', 'utils.validators', 'utils.modern_dialogs', 'utils.loading']
binaries += collect_dynamic_libs('PySide6')
tmp_ret = collect_all('firebase_admin')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('google.auth')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('google.cloud')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
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
    name='SOT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ui/logo.ico',
)
