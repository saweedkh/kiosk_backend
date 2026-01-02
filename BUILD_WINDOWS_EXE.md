# ساخت EXE برای Windows

## ⚠️ نکته مهم

PyInstaller نمی‌تواند EXE برای Windows روی Mac/Linux بسازد. برای ساخت EXE واقعی، باید روی Windows build کنید.

## روش‌های ساخت EXE برای Windows

### روش 1: استفاده از GitHub Actions (توصیه می‌شود) ✅

این روش به صورت خودکار EXE را روی Windows build می‌کند:

1. **Push کردن کد به GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Windows build"
   git push
   ```

2. **اجرای Workflow:**
   - به GitHub repository بروید
   - به بخش "Actions" بروید
   - Workflow "Build Windows EXE" را انتخاب کنید
   - روی "Run workflow" کلیک کنید

3. **دانلود EXE:**
   - بعد از اتمام build، به بخش "Artifacts" بروید
   - فایل `kiosk-windows-exe` را دانلود کنید
   - فایل `kiosk.exe` داخل آن است

### روش 2: Build روی Windows مستقیم

اگر به یک ماشین Windows دسترسی دارید:

```cmd
# 1. Clone پروژه
git clone <repository-url>
cd kiosk

# 2. ایجاد virtual environment
python -m venv venv
venv\Scripts\activate

# 3. نصب dependencies
pip install -r requirements/base.txt

# 4. آماده‌سازی
python manage.py migrate
python manage.py collectstatic --noinput

# 5. Build EXE
pyinstaller kiosk.spec --clean --noconfirm
```

فایل EXE در `dist\kiosk.exe` قرار دارد.

### روش 3: استفاده از ماشین مجازی Windows

1. یک VM Windows نصب کنید (VirtualBox, VMware, Parallels)
2. پروژه را در VM کپی کنید
3. مراحل روش 2 را در VM اجرا کنید

### روش 4: استفاده از Docker (پیشرفته)

می‌توانید از Windows container در Docker استفاده کنید، اما این پیچیده است.

## تنظیمات Spec File

Spec file به صورت خودکار نام فایل را `.exe` تنظیم می‌کند اگر روی Windows build شود.

## نتیجه

| روش | نیاز به Windows | خودکار | توصیه |
|-----|----------------|--------|--------|
| GitHub Actions | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| Build مستقیم | ✅ | ❌ | ⭐⭐⭐⭐ |
| VM | ✅ | ❌ | ⭐⭐⭐ |
| Docker | ❌ | ⚠️ | ⭐⭐ |

**بهترین روش:** استفاده از GitHub Actions - بدون نیاز به Windows و کاملاً خودکار!

