# 🚀 ساخت EXE برای Windows

## ⚠️ نکته مهم

**PyInstaller نمی‌تواند EXE برای Windows روی Mac/Linux بسازد!**

برای ساخت EXE واقعی برای Windows، باید از یکی از روش‌های زیر استفاده کنید:

## ✅ روش 1: GitHub Actions (توصیه می‌شود)

این روش به صورت **خودکار** EXE را روی Windows build می‌کند:

### مراحل:

1. **Push کردن کد به GitHub:**
   ```bash
   git add .
   git commit -m "Add Windows build workflow"
   git push
   ```

2. **اجرای Workflow:**
   - به GitHub repository بروید
   - به بخش **"Actions"** بروید
   - Workflow **"Build Windows EXE"** را انتخاب کنید
   - روی **"Run workflow"** کلیک کنید

3. **دانلود EXE:**
   - بعد از اتمام build (حدود 5-10 دقیقه)
   - به بخش **"Artifacts"** بروید
   - فایل `kiosk-windows-exe` را دانلود کنید
   - فایل `kiosk.exe` داخل آن است ✅

### مزایا:
- ✅ بدون نیاز به Windows
- ✅ کاملاً خودکار
- ✅ همیشه EXE واقعی برای Windows
- ✅ رایگان (GitHub Actions)

## ✅ روش 2: Build روی Windows مستقیم

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

## 📋 خلاصه

| روش | نیاز به Windows | خودکار | زمان |
|-----|----------------|--------|------|
| **GitHub Actions** | ❌ | ✅ | 5-10 دقیقه |
| Build مستقیم | ✅ | ❌ | 2-5 دقیقه |
| VM | ✅ | ❌ | 10-15 دقیقه |

**بهترین روش:** استفاده از GitHub Actions ⭐

## 🔄 Workflow خودکار

Workflow به صورت خودکار در این موارد اجرا می‌شود:
- Push به branch `main`
- تغییر در `kiosk.spec` یا `kiosk_main.py`
- ایجاد Release

همچنین می‌توانید به صورت دستی از Actions tab اجرا کنید.

