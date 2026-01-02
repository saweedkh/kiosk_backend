#!/usr/bin/env python
"""
اسکریپت برای بررسی حجم EXE و محتویات آن
"""
import os
from pathlib import Path

def format_size(size_bytes):
    """تبدیل بایت به فرمت خوانا"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def check_exe():
    """بررسی فایل EXE"""
    exe_path = Path('dist/kiosk.exe')
    
    if not exe_path.exists():
        print("❌ فایل EXE پیدا نشد!")
        print("   مسیر: dist/kiosk.exe")
        return
    
    # حجم EXE
    exe_size = exe_path.stat().st_size
    print(f"✅ فایل EXE پیدا شد")
    print(f"   مسیر: {exe_path.absolute()}")
    print(f"   حجم: {format_size(exe_size)}")
    print()
    
    # بررسی staticfiles
    staticfiles_path = Path('staticfiles')
    if staticfiles_path.exists():
        # محاسبه حجم staticfiles
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(staticfiles_path):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
                file_count += 1
        
        print(f"📦 پوشه staticfiles:")
        print(f"   مسیر: {staticfiles_path.absolute()}")
        print(f"   حجم: {format_size(total_size)}")
        print(f"   تعداد فایل: {file_count}")
        print()
        
        # بررسی اینکه آیا داخل EXE قرار گرفته
        if exe_size > 50 * 1024 * 1024:  # بیشتر از 50MB
            print("✅ حجم EXE بزرگ است - احتمالاً staticfiles داخل آن است")
        else:
            print("⚠️  حجم EXE کوچک است - ممکن است staticfiles داخل آن نباشد")
            print("   بررسی کنید که در spec file درست اضافه شده باشد")
    else:
        print("❌ پوشه staticfiles پیدا نشد!")
        print("   ابتدا باید collectstatic را اجرا کنید")

if __name__ == '__main__':
    check_exe()

