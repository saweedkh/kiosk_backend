# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file برای ساخت EXE پروژه Kiosk
"""

import sys
from pathlib import Path

# مسیر پروژه - SPECPATH توسط PyInstaller تنظیم می‌شود
try:
    project_root = Path(SPECPATH)
except NameError:
    project_root = Path.cwd()

block_cipher = None

# بررسی وجود staticfiles
staticfiles_path = project_root / 'staticfiles'
staticfiles_abs = staticfiles_path.resolve()

if not staticfiles_path.exists():
    print("⚠️  هشدار: پوشه staticfiles پیدا نشد!")
    print(f"   مسیر مورد انتظار: {staticfiles_path}")
    print("   لطفاً ابتدا 'python manage.py collectstatic' را اجرا کنید")
else:
    # محاسبه حجم برای نمایش
    import os
    total_size = sum(f.stat().st_size for f in staticfiles_path.rglob('*') if f.is_file())
    print(f"✅ staticfiles پیدا شد: {staticfiles_abs}")
    print(f"   حجم: {total_size / 1024 / 1024:.2f} MB")

# جمع‌آوری تمام فایل‌های Python
# ساخت لیست datas با فیلتر کردن None ها
datas_list = []
if (project_root / 'pna.pcpos.dll').exists():
    datas_list.append((str((project_root / 'pna.pcpos.dll').resolve()), '.'))
if (project_root / 'env.example').exists():
    datas_list.append((str((project_root / 'env.example').resolve()), '.'))
if staticfiles_path.exists():
    # استفاده از مسیر absolute برای اطمینان
    datas_list.append((str(staticfiles_abs), 'staticfiles'))
    print(f"✅ staticfiles به datas اضافه شد")
else:
    print("❌ staticfiles پیدا نشد! حجم EXE کوچک خواهد بود.")

a = Analysis(
    ['kiosk_main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'django',
        'django.core',
        'django.core.management',
        'django.core.management.commands',
        'django.core.management.commands.runserver',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'rest_framework_simplejwt',
        'corsheaders',
        'django_filters',
        'drf_spectacular',
        'apps.products',
        'apps.orders',
        'apps.payment',
        'apps.logs',
        'apps.admin_panel',
        'apps.core',
        'config',
        'config.settings',
        'config.urls',
        'config.wsgi',
        'PIL',
        'PIL._tkinter_finder',
        'reportlab',
        'openpyxl',
        'jdatetime',
        'pythonnet',
        'serial',  # pyserial به صورت serial import می‌شود
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# فایل‌های اضافی که باید کپی شوند
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ساخت EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='kiosk',  # PyInstaller خودش .exe را روی Windows اضافه می‌کند
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # غیرفعال کردن UPX برای بررسی حجم واقعی
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # نمایش console برای لاگ‌ها
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # می‌توانید یک فایل .ico اضافه کنید
)

