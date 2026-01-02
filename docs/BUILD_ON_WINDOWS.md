# ساخت EXE روی Windows

## ⚠️ نکته مهم

**PyInstaller نمی‌تواند EXE برای Windows روی Mac/Linux بسازد!**

فایل تولید شده روی Mac یک **Mach-O executable** است (برای Mac) نه EXE (برای Windows).

## راه‌حل‌ها

### روش 1: Build روی Windows (توصیه می‌شود) ✅

1. پروژه را به یک ماشین Windows منتقل کنید
2. Python و dependencies را نصب کنید
3. Build را اجرا کنید:

```cmd
venv\Scripts\activate
build_exe.bat
```

یا:

```cmd
venv\Scripts\activate
python manage.py collectstatic --noinput
pyinstaller kiosk.spec --clean --noconfirm
```

### روش 2: استفاده از ماشین مجازی Windows

1. یک VM Windows نصب کنید (VirtualBox, VMware, Parallels)
2. پروژه را در VM کپی کنید
3. Build را در VM اجرا کنید

### روش 3: استفاده از GitHub Actions یا CI/CD

می‌توانید از GitHub Actions برای build خودکار روی Windows استفاده کنید.

## فایل فعلی (روی Mac)

فایل `dist/kiosk` که روی Mac build شده:
- ✅ یک **Mac executable** است
- ✅ روی Mac قابل اجرا است
- ❌ روی Windows کار نمی‌کند
- ❌ EXE نیست

برای تست روی Mac:
```bash
./dist/kiosk
```

اما برای Windows باید روی Windows build کنید!

## خلاصه

| Platform | Build روی | خروجی | قابل اجرا روی |
|----------|-----------|-------|---------------|
| Windows | Windows | `kiosk.exe` | Windows ✅ |
| Mac | Mac | `kiosk` (Mach-O) | Mac ✅ |
| Linux | Linux | `kiosk` (ELF) | Linux ✅ |

**نتیجه:** برای EXE واقعی، باید روی Windows build کنید!

