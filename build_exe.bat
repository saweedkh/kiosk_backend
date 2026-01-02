@echo off
REM Script برای ساخت EXE پروژه Kiosk روی ویندوز
REM این فایل باید در محیط virtual environment اجرا شود

echo ========================================
echo ساخت EXE پروژه Kiosk
echo ========================================
echo.

REM بررسی وجود virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo خطا: virtual environment پیدا نشد!
    echo لطفاً ابتدا virtual environment را ایجاد کنید:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    pause
    exit /b 1
)

REM فعال کردن virtual environment
call venv\Scripts\activate.bat

REM بررسی نصب PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo نصب PyInstaller...
    pip install pyinstaller==6.3.0
)

REM اجرای migrations (برای اطمینان از وجود دیتابیس)
echo.
echo اجرای migrations...
python manage.py migrate --noinput

REM جمع‌آوری static files
echo.
echo جمع‌آوری static files...
python manage.py collectstatic --noinput

REM ساخت EXE
echo.
echo ساخت EXE...
pyinstaller kiosk.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo خطا در ساخت EXE!
    pause
    exit /b 1
)

echo.
echo ========================================
echo ساخت EXE با موفقیت انجام شد!
echo ========================================
echo.
echo فایل EXE در پوشه dist\kiosk.exe قرار دارد
echo.
echo برای اجرا:
echo   dist\kiosk.exe
echo.
pause

