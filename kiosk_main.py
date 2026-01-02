#!/usr/bin/env python
"""
Entry point برای اجرای Kiosk به صورت EXE
این فایل برای PyInstaller استفاده می‌شود
"""
import os
import sys
from pathlib import Path

# تنظیم DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# اگر در حالت EXE هستیم، مسیرهای لازم را تنظیم کن
if getattr(sys, 'frozen', False):
    # PyInstaller bundle
    # sys._MEIPASS مسیر موقت است که PyInstaller فایل‌های extract شده را قرار می‌دهد
    MEIPASS = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
    BASE_DIR = Path(sys.executable).parent
    
    # اضافه کردن مسیر EXE به sys.path
    if BASE_DIR not in [Path(p) for p in sys.path]:
        sys.path.insert(0, str(BASE_DIR))
    
    # تنظیم مسیر برای static files - از داخل EXE استفاده می‌کنیم
    # فایل‌های staticfiles در sys._MEIPASS/staticfiles قرار دارند
    os.environ['STATIC_ROOT'] = str(MEIPASS / 'staticfiles')
    # Media و logs در کنار EXE (چون باید writable باشند)
    os.environ['MEDIA_ROOT'] = str(BASE_DIR / 'media')
    os.environ['LOGS_DIR'] = str(BASE_DIR / 'logs')

def main():
    """اجرای سرور Django"""
    try:
        import django
        from django.core.management import execute_from_command_line
        
        # Initialize Django
        django.setup()
        
        # اجرای runserver
        # می‌توانیم از gunicorn هم استفاده کنیم اما برای EXE runserver ساده‌تر است
        from django.core.management.commands.runserver import Command as RunserverCommand
        
        # تنظیمات پیش‌فرض
        default_addr = os.getenv('SERVER_ADDR', '127.0.0.1')
        default_port = os.getenv('SERVER_PORT', '8000')
        
        # اجرای سرور
        execute_from_command_line([
            'kiosk_main.py',
            'runserver',
            f'{default_addr}:{default_port}',
            '--noreload',  # در حالت EXE reload لازم نیست
        ])
        
    except KeyboardInterrupt:
        print('\n\nسرور متوقف شد.')
        sys.exit(0)
    except Exception as e:
        print(f'خطا در اجرای سرور: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

