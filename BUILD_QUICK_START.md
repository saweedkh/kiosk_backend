# راهنمای سریع ساخت EXE

## 🚀 روش ساده (توصیه می‌شود)

### روی ویندوز:

```cmd
# 1. فعال کردن virtual environment
venv\Scripts\activate

# 2. اجرای batch file
build_exe.bat
```

### روی Mac/Linux:

```bash
# 1. فعال کردن virtual environment
source venv/bin/activate

# 2. اجرای shell script
./build_exe.sh
```

**⚠️ توجه:** روی Mac/Linux یک **Mac/Linux executable** ساخته می‌شود (نه EXE)!

برای ساخت EXE واقعی برای Windows، باید روی **Windows** build کنید!

---

## 📝 روش دستی (گام به گام)

### 1. آماده‌سازی

```cmd
# فعال کردن virtual environment
venv\Scripts\activate

# نصب PyInstaller (اگر نصب نیست)
pip install pyinstaller==6.3.0

# اجرای migrations
python manage.py migrate

# جمع‌آوری static files
python manage.py collectstatic --noinput
```

### 2. ساخت EXE

**روی ویندوز:**
```cmd
# حذف پوشه‌های قبلی
rmdir /s /q build dist

# ساخت EXE
pyinstaller kiosk.spec --clean --noconfirm
```

**روی Mac/Linux:**
```bash
# حذف پوشه‌های قبلی
rm -rf build dist

# ساخت EXE
pyinstaller kiosk.spec --clean --noconfirm
```

### 3. نتیجه

فایل EXE در پوشه `dist\kiosk.exe` قرار دارد.

---

## 🐧 روی Linux/Mac (برای تست)

```bash
# فعال کردن virtual environment
source venv/bin/activate

# نصب PyInstaller
pip install pyinstaller==6.3.0

# آماده‌سازی
python manage.py migrate
python manage.py collectstatic --noinput

# ساخت EXE (برای ویندوز)
pyinstaller kiosk.spec --clean --noconfirm
```

**نکته:** برای ساخت EXE ویندوز روی Linux/Mac، نیاز به Wine دارید.

---

## ✅ بررسی نتیجه

بعد از ساخت، بررسی کنید:

```
dist/
├── kiosk.exe          ✅ فایل اجرایی
└── (فایل‌های دیگر PyInstaller)
```

**حجم EXE:** معمولاً 50-100 مگابایت (شامل staticfiles)

---

## 🔧 عیب‌یابی

### خطا: PyInstaller پیدا نشد
```cmd
pip install pyinstaller==6.3.0
```

### خطا: staticfiles پیدا نشد
```cmd
python manage.py collectstatic --noinput
```

### خطا: migrations
```cmd
python manage.py migrate
```

---

## 📦 فایل‌های نهایی

بعد از ساخت، فقط این فایل را نیاز دارید:
- ✅ `dist\kiosk.exe` - این فایل شامل همه چیز است!

**دیگر نیازی به:**
- ❌ staticfiles (داخل EXE است)
- ❌ pna.pcpos.dll (اگر در spec اضافه شده باشد)

**هنوز نیاز دارید:**
- ✅ `.env` (باید خودتان ایجاد کنید)

