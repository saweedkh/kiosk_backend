#!/usr/bin/env python
"""
اسکریپت تست برای بررسی اینکه staticfiles در spec file درست اضافه می‌شود
"""
import sys
from pathlib import Path

# شبیه‌سازی SPECPATH
SPECPATH = Path.cwd()
project_root = Path(SPECPATH)

# بررسی وجود staticfiles
staticfiles_path = project_root / 'staticfiles'
print(f"Project root: {project_root}")
print(f"Staticfiles path: {staticfiles_path}")
print(f"Exists: {staticfiles_path.exists()}")

if staticfiles_path.exists():
    # محاسبه حجم
    total_size = 0
    file_count = 0
    for item in staticfiles_path.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size
            file_count += 1
    
    print(f"Total files: {file_count}")
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
    
    # بررسی ساختار
    print("\nStructure:")
    for item in staticfiles_path.iterdir():
        if item.is_dir():
            print(f"  📁 {item.name}/")
        else:
            print(f"  📄 {item.name}")
else:
    print("❌ staticfiles not found!")

