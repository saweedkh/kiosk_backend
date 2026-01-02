# عیب‌یابی ساخت EXE

## مشکل: حجم EXE کوچک است (staticfiles داخل نیست)

### علت
فایل‌های `staticfiles` داخل EXE قرار نگرفته‌اند.

### راه حل

#### 1. بررسی وجود staticfiles

```cmd
# بررسی وجود پوشه staticfiles
dir staticfiles
```

اگر پوشه وجود ندارد:
```cmd
python manage.py collectstatic --noinput
```

#### 2. بررسی spec file

مطمئن شوید در `kiosk.spec` این خط وجود دارد:
```python
datas=[
    (str(staticfiles_path), 'staticfiles'),
]
```

#### 3. ساخت مجدد EXE

```cmd
# حذف پوشه‌های قبلی
rmdir /s /q build dist

# ساخت مجدد
pyinstaller kiosk.spec --clean --noconfirm
```

#### 4. بررسی حجم EXE

بعد از ساخت، حجم EXE باید **حدود 50-100 مگابایت** باشد (بسته به staticfiles).

```cmd
dir dist\kiosk.exe
```

### بررسی اینکه staticfiles داخل EXE است

1. **بررسی حجم:**
   - بدون staticfiles: ~30-50 MB
   - با staticfiles: ~50-100 MB

2. **تست اجرا:**
   - EXE را اجرا کنید
   - به `http://localhost:8000` بروید
   - اگر صفحات به درستی نمایش داده می‌شوند، staticfiles داخل EXE است
   - اگر صفحات خالی هستند، staticfiles داخل EXE نیست

3. **بررسی sys._MEIPASS:**
   می‌توانید یک اسکریپت تست بنویسید:
   ```python
   import sys
   if getattr(sys, 'frozen', False):
       import os
       meipass = sys._MEIPASS
       staticfiles_path = os.path.join(meipass, 'staticfiles')
       if os.path.exists(staticfiles_path):
           print("✅ staticfiles داخل EXE است")
       else:
           print("❌ staticfiles داخل EXE نیست")
   ```

## مشکل: خطا در ساخت EXE

### خطا: "staticfiles not found"

**راه حل:**
```cmd
python manage.py collectstatic --noinput
```

### خطا: "PyInstaller not found"

**راه حل:**
```cmd
pip install pyinstaller==6.3.0
```

### خطا: "No module named 'xxx'"

**راه حل:**
مطمئن شوید تمام dependencies نصب شده‌اند:
```cmd
pip install -r requirements/base.txt
```

## بهینه‌سازی حجم EXE

### کاهش حجم (اگر خیلی بزرگ است)

1. **حذف فایل‌های غیرضروری از staticfiles:**
   - فایل‌های test
   - فایل‌های source map

2. **استفاده از UPX:**
   در spec file:
   ```python
   upx=True,  # فشرده‌سازی
   ```

3. **حذف ماژول‌های غیرضروری:**
   در spec file:
   ```python
   excludes=[
       'matplotlib',
       'numpy',
       'pandas',
       'scipy',
       'IPython',
       'jupyter',
       'tkinter',
   ],
   ```

## نکات مهم

1. ✅ **همیشه** قبل از ساخت EXE، `collectstatic` را اجرا کنید
2. ✅ حجم EXE باید **حدود 50-100 MB** باشد (با staticfiles)
3. ✅ بعد از ساخت، EXE را تست کنید
4. ✅ مطمئن شوید صفحات وب به درستی نمایش داده می‌شوند

