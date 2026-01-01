# راهنمای راه‌اندازی و اتصال به پرینتر شبکه

این مستند شامل راهنمای کامل برای اتصال به پرینتر شبکه و ارسال دستورات چاپ است.

**استفاده از کتابخانه `python-escpos` برای چاپ استاندارد ESC/POS**

## پیش‌نیازها

1. پرینتر باید به شبکه متصل باشد و IP داشته باشد
2. پرینتر باید از پروتکل Raw TCP/IP Printing پشتیبانی کند (پورت 9100)
3. سرور باید به همان شبکه متصل باشد
4. کتابخانه `python-escpos` نصب شده باشد (به صورت خودکار در requirements/base.txt موجود است)

## تنظیمات

### 1. تنظیمات در `.env`:

```env
# فعال کردن چاپ
PRINTER_ENABLED=True

# آدرس IP پرینتر
PRINTER_IP=192.168.1.100

# پورت پرینتر (پیش‌فرض: 9100)
PRINTER_PORT=9100

# Timeout اتصال (ثانیه)
PRINTER_TIMEOUT=5

# استفاده از دستورات ESC/POS (برای پرینترهای حرارتی)
PRINTER_USE_ESCPOS=True

# تبدیل متن فارسی به تصویر برای پرینترهای حرارتی؟
# True: تبدیل متن فارسی به تصویر و ارسال به پرینتر (توصیه می‌شود)
# False: ارسال مستقیم متن UTF-8 یا CP864 (بسته به PRINTER_USE_CP864)
PRINTER_USE_IMAGE_FOR_PERSIAN=True

# استفاده از کدگذاری CP864 برای متن فارسی؟
# True: استفاده از CP864 encoding (برای پرینترهای حرارتی که از CP864 پشتیبانی می‌کنند)
# False: استفاده از UTF-8 یا تبدیل به تصویر (بسته به PRINTER_USE_IMAGE_FOR_PERSIAN)
# نکته: اگر PRINTER_USE_IMAGE_FOR_PERSIAN=True باشد، این تنظیم نادیده گرفته می‌شود
PRINTER_USE_CP864=False
```

### 2. پیدا کردن IP پرینتر

#### روش 1: از تنظیمات پرینتر
- به تنظیمات پرینتر بروید
- بخش Network یا TCP/IP را پیدا کنید
- IP Address را یادداشت کنید

#### روش 2: از طریق Router
- به پنل مدیریت Router بروید
- لیست دستگاه‌های متصل را ببینید
- پرینتر را پیدا کنید

#### روش 3: از طریق Command Line (Linux/Mac)
```bash
# اسکن شبکه برای پیدا کردن پرینتر
nmap -p 9100 192.168.1.0/24
```

#### روش 4: از طریق Command Line (Windows)
```powershell
# اسکن شبکه
Test-NetConnection -ComputerName 192.168.1.100 -Port 9100
```

## تست اتصال

### 1. تست با Management Command

```bash
python manage.py test_printer
```

این دستور:
- اتصال به پرینتر را تست می‌کند
- یک تست چاپ ارسال می‌کند
- نتیجه را نمایش می‌دهد

### 2. تست دستی با Telnet

```bash
# Linux/Mac
telnet 192.168.1.100 9100

# Windows
telnet 192.168.1.100 9100
```

اگر اتصال برقرار شد، می‌توانید دستورات را مستقیماً تایپ کنید.

### 3. تست با Python

```python
import socket

printer_ip = "192.168.1.100"
printer_port = 9100

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((printer_ip, printer_port))
    print("✅ اتصال موفق!")
    sock.close()
except Exception as e:
    print(f"❌ خطا: {e}")
```

## پروتکل‌های چاپ

### 1. Raw TCP/IP Printing (پورت 9100)
- **رایج‌ترین روش** برای پرینترهای شبکه
- مستقیماً داده را به پرینتر ارسال می‌کند
- پشتیبانی از:
  - **PDF**: برای پرینترهای معمولی که از PDF پشتیبانی می‌کنند
  - **ESC/POS**: برای پرینترهای حرارتی
  - **Plain Text**: برای پرینترهای ساده

### 2. LPR/LPD (پورت 515)
- پروتکل قدیمی‌تر
- نیاز به نصب LPR client

### 3. IPP (پورت 631)
- Internet Printing Protocol
- نیاز به پشتیبانی از HTTP

## دستورات ESC/POS

برای پرینترهای حرارتی، از دستورات ESC/POS استفاده می‌شود:

### دستورات اصلی:

```python
# Initialize printer
ESC + '@'  # Reset printer

# Text formatting
ESC + 'E' + '\x01'  # Bold ON
ESC + 'E' + '\x00'  # Bold OFF

# Alignment
ESC + 'a' + '\x00'  # Left
ESC + 'a' + '\x01'  # Center
ESC + 'a' + '\x02'  # Right

# Line feed
'\n'  # Single line
'\n\n'  # Double line

# Cut paper
GS + 'V' + '\x41' + '\x03'  # Full cut
```

## مثال‌های عملی

### مثال 1: چاپ متن ساده

```python
from apps.orders.services.print_service import PrintService

# متن ساده
text = "تست چاپ\n\nاین یک تست است\n\n"
data = text.encode('utf-8')

# ارسال به پرینتر
success = PrintService.send_to_printer(
    data=data,
    printer_ip='192.168.1.100',
    printer_port=9100,
    timeout=5
)
```

### مثال 2: چاپ رسید کامل

```python
from apps.orders.models import Order
from apps.orders.services.print_service import PrintService

# دریافت سفارش
order = Order.objects.get(order_number='ORD-20240115-1234')

# چاپ رسید
success = PrintService.print_receipt(order)
```

### مثال 3: استفاده از API

```bash
# دریافت داده رسید
curl -X GET http://localhost:8000/api/kiosk/orders/receipt/ORD-20240115-1234/

# چاپ رسید
curl -X POST http://localhost:8000/api/kiosk/orders/receipt/ORD-20240115-1234/
```

## عیب‌یابی

### مشکل 1: اتصال برقرار نمی‌شود

**علل احتمالی:**
- IP پرینتر اشتباه است
- پرینتر به شبکه متصل نیست
- Firewall مانع اتصال است
- پورت اشتباه است

**راه حل:**
1. IP پرینتر را بررسی کنید
2. با `ping` تست کنید: `ping 192.168.1.100`
3. با `telnet` تست کنید: `telnet 192.168.1.100 9100`
4. Firewall را بررسی کنید

### مشکل 2: چاپ می‌شود اما متن درست نیست

**علل احتمالی:**
- Encoding اشتباه است
- پرینتر از ESC/POS پشتیبانی نمی‌کند

**راه حل:**
1. `PRINTER_ENCODING` را بررسی کنید (باید `utf-8` باشد)
2. `PRINTER_USE_ESCPOS` را `False` کنید برای Plain Text

### مشکل 3: Timeout

**علل احتمالی:**
- پرینتر پاسخ نمی‌دهد
- شبکه کند است

**راه حل:**
1. `PRINTER_TIMEOUT` را افزایش دهید
2. اتصال شبکه را بررسی کنید

### مشکل 4: چاپ نمی‌شود اما خطا نمی‌دهد

**علل احتمالی:**
- `PRINTER_ENABLED=False` است
- پرینتر در حالت Sleep است

**راه حل:**
1. `.env` را بررسی کنید
2. پرینتر را از حالت Sleep خارج کنید

## تست با Management Command

یک دستور مدیریتی برای تست اتصال و چاپ:

```bash
python manage.py test_printer
```

این دستور:
- تنظیمات پرینتر را نمایش می‌دهد
- اتصال را تست می‌کند
- یک تست چاپ ارسال می‌کند
- نتیجه را نمایش می‌دهد

## نکات مهم

1. **پورت 9100**: اکثر پرینترهای شبکه از پورت 9100 برای Raw TCP/IP Printing استفاده می‌کنند
2. **ESC/POS**: برای پرینترهای حرارتی (POS printers) استفاده می‌شود
3. **Encoding**: برای متن فارسی باید `utf-8` باشد
4. **Timeout**: برای شبکه‌های کند، timeout را افزایش دهید
5. **Firewall**: مطمئن شوید که Firewall مانع اتصال نمی‌شود
6. **چاپ فارسی**: برای پرینترهای حرارتی که فونت فارسی ندارند، از `PRINTER_USE_IMAGE_FOR_PERSIAN=True` استفاده کنید (متن به تصویر تبدیل می‌شود)

## پشتیبانی از پرینترهای مختلف

### پرینترهای حرارتی (Thermal Printers)
- از ESC/POS استفاده می‌کنند
- `PRINTER_USE_ESCPOS=True`
- برای چاپ فارسی: `PRINTER_USE_IMAGE_FOR_PERSIAN=True` (توصیه می‌شود)
- مثال: Epson TM-T20, Star TSP100

**نکته مهم برای چاپ فارسی:**
- اکثر پرینترهای حرارتی به صورت پیش‌فرض فونت فارسی ندارند
- با `PRINTER_USE_IMAGE_FOR_PERSIAN=True`، متن فارسی به تصویر تبدیل شده و به صورت bitmap چاپ می‌شود
- این روش بهترین راه برای چاپ صحیح فارسی در پرینترهای حرارتی است
- ارتفاع تصویر 30px است که برای پرینترهای حرارتی بهینه است

### پرینترهای معمولی (Laser/Inkjet)
- می‌توانند از Plain Text استفاده کنند
- `PRINTER_USE_ESCPOS=False`

## مثال کامل

```python
# تنظیمات در .env
PRINTER_ENABLED=True
PRINTER_IP=192.168.1.100
PRINTER_PORT=9100
PRINTER_TIMEOUT=5
PRINTER_CHAR_CODE=CP864  # کدگذاری برای متن فارسی (CP864 یا CP720)

# استفاده در کد
from apps.orders.models import Order
from apps.orders.services.print_service import PrintService

order = Order.objects.get(order_number='ORD-20240115-1234')
if order.payment_status == 'paid':
    success = PrintService.print_receipt(order)
    if success:
        print("✅ رسید با موفقیت چاپ شد")
    else:
        print("❌ خطا در چاپ رسید")
```

## منابع

- [ESC/POS Command Reference](https://reference.epson-biz.com/modules/ref_escpos/)
- [Raw TCP/IP Printing](https://en.wikipedia.org/wiki/Network_printing)
- [Python Socket Programming](https://docs.python.org/3/library/socket.html)

