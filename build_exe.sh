#!/bin/bash
# Script برای ساخت EXE پروژه Kiosk روی Mac/Linux
# این فایل باید در محیط virtual environment اجرا شود

echo "========================================"
echo "ساخت EXE پروژه Kiosk"
echo "========================================"
echo ""

# بررسی وجود virtual environment
if [ ! -d "venv" ]; then
    echo "خطا: virtual environment پیدا نشد!"
    echo "لطفاً ابتدا virtual environment را ایجاد کنید:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    exit 1
fi

# فعال کردن virtual environment
source venv/bin/activate

# بررسی نصب PyInstaller
python -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "نصب PyInstaller..."
    pip install pyinstaller==6.3.0
fi

# اجرای migrations (برای اطمینان از وجود دیتابیس)
echo ""
echo "اجرای migrations..."
python manage.py migrate --noinput

# جمع‌آوری static files
echo ""
echo "جمع‌آوری static files..."
python manage.py collectstatic --noinput

# حذف پوشه‌های قبلی
echo ""
echo "حذف پوشه‌های قبلی..."
rm -rf build dist

# ساخت EXE
echo ""
echo "ساخت EXE..."
pyinstaller kiosk.spec --clean --noconfirm

if [ $? -ne 0 ]; then
    echo ""
    echo "خطا در ساخت EXE!"
    exit 1
fi

echo ""
echo "========================================"
echo "ساخت EXE با موفقیت انجام شد!"
echo "========================================"
echo ""
echo "⚠️  توجه: این فایل یک Mac executable است (نه EXE برای Windows)"
echo "فایل در پوشه dist/kiosk قرار دارد"
echo ""
echo "برای ساخت EXE واقعی برای Windows، باید روی Windows build کنید!"
echo "برای تست روی Mac: ./dist/kiosk"
echo ""

