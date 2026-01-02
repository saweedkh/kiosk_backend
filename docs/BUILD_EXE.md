# راهنمای ساخت EXE برای ویندوز

این راهنما نحوه ساخت فایل EXE از پروژه Kiosk را توضیح می‌دهد.

## پیش‌نیازها

1. **Python 3.9+** نصب شده باشد
2. **Virtual Environment** ایجاد شده باشد
3. تمام **Dependencies** نصب شده باشند

## مراحل ساخت EXE

### 1. آماده‌سازی محیط

```bash
# فعال کردن virtual environment
venv\Scripts\activate

# نصب dependencies
pip install -r requirements/base.txt
```

### 2. آماده‌سازی پروژه

```bash
# اجرای migrations
python manage.py migrate

# جمع‌آوری static files
python manage.py collectstatic --noinput

# کپی کردن فایل‌های build فرانت (اگر لازم است)
python manage.py copy_frontend_build
```

### 3. ساخت EXE

#### روش 1: استفاده از batch file (ساده‌تر)

```bash
build_exe.bat
```

#### روش 2: استفاده از PyInstaller مستقیم

```bash
# ساخت EXE
pyinstaller kiosk.spec --clean --noconfirm
```

### 4. بررسی خروجی

فایل EXE در پوشه `dist/kiosk.exe` ایجاد می‌شود.

## ساختار فایل EXE

پس از ساخت، پوشه `dist` شامل موارد زیر است:

```
dist/
├── kiosk.exe              # فایل اجرایی اصلی
├── staticfiles/           # فایل‌های static
├── media/                 # فایل‌های media (اگر وجود دارد)
├── pna.pcpos.dll         # DLL کارت‌خوان
├── env.example            # فایل نمونه تنظیمات
└── logs/                  # پوشه لاگ‌ها (خودکار ایجاد می‌شود)
```

## اجرای EXE

### روش 1: اجرای مستقیم

```bash
dist\kiosk.exe
```

سرور به صورت پیش‌فرض روی `127.0.0.1:8000` اجرا می‌شود.

### روش 2: با تنظیمات محیطی

می‌توانید یک فایل `.env` در کنار `kiosk.exe` قرار دهید:

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
SERVER_PORT=8000
SERVER_ADDR=127.0.0.1
```

## تنظیمات مهم

### مسیرهای فایل

در حالت EXE، مسیرها به صورت خودکار تنظیم می‌شوند:
- `BASE_DIR`: مسیر پوشه حاوی `kiosk.exe`
- `STATIC_ROOT`: `BASE_DIR/staticfiles`
- `MEDIA_ROOT`: `BASE_DIR/media`
- `LOGS_DIR`: `BASE_DIR/logs`

### دیتابیس

فایل `db.sqlite3` در کنار `kiosk.exe` ایجاد می‌شود.

### Static Files

فایل‌های static باید قبل از ساخت EXE با `collectstatic` جمع‌آوری شوند.

## عیب‌یابی

### مشکل: EXE اجرا نمی‌شود

1. بررسی کنید که تمام فایل‌های لازم در پوشه `dist` وجود دارند
2. بررسی کنید که `pna.pcpos.dll` در کنار EXE قرار دارد
3. لاگ‌ها را در پوشه `logs/` بررسی کنید

### مشکل: Static files نمایش داده نمی‌شوند

1. مطمئن شوید که `collectstatic` قبل از ساخت EXE اجرا شده است
2. بررسی کنید که پوشه `staticfiles` در `dist` وجود دارد

### مشکل: دیتابیس کار نمی‌کند

1. بررسی کنید که `db.sqlite3` در کنار EXE وجود دارد
2. اگر وجود ندارد، EXE را یک بار اجرا کنید تا ایجاد شود
3. یا فایل `db.sqlite3` را از پروژه اصلی کپی کنید

### مشکل: DLL کارت‌خوان کار نمی‌کند

1. بررسی کنید که `pna.pcpos.dll` در کنار EXE قرار دارد
2. بررسی کنید که `.NET Framework` یا `Mono` نصب است
3. برای `pythonnet` ممکن است نیاز به تنظیمات اضافی باشد

## بهینه‌سازی

### کاهش حجم EXE

می‌توانید در `kiosk.spec` موارد زیر را اضافه کنید:

```python
excludes=[
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    'tkinter',
    'test',
    'unittest',
]
```

### ساخت EXE بدون Console

برای ساخت EXE بدون پنجره console، در `kiosk.spec` تغییر دهید:

```python
console=False,  # به جای True
```

## نکات مهم

1. **همیشه** قبل از ساخت EXE، `collectstatic` را اجرا کنید
2. فایل `.env` را در کنار EXE قرار دهید (نه درون EXE)
3. فایل `db.sqlite3` باید در کنار EXE باشد
4. برای production، `DEBUG=False` را تنظیم کنید
5. `SECRET_KEY` را در `.env` تنظیم کنید

## ساخت Installer

برای ساخت installer (مثلاً با Inno Setup یا NSIS):

1. تمام محتویات پوشه `dist` را در یک پوشه قرار دهید
2. از installer builder استفاده کنید
3. مطمئن شوید که تمام فایل‌های لازم شامل شوند:
   - `kiosk.exe`
   - `staticfiles/`
   - `media/` (اگر لازم است)
   - `pna.pcpos.dll`
   - `env.example`

## پشتیبانی

در صورت بروز مشکل، لاگ‌ها را در پوشه `logs/` بررسی کنید.

