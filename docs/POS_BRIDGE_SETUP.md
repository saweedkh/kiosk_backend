# راهنمای راه‌اندازی POS Bridge Service

این راهنما نحوه راه‌اندازی سرویس Bridge برای اتصال به دستگاه POS از طریق سیستم ویندوزی را توضیح می‌دهد.

## 📋 خلاصه

POS Bridge Service یک سرویس HTTP است که روی سیستم ویندوزی اجرا می‌شود و از DLL برای ارتباط با دستگاه POS استفاده می‌کند. سیستم‌های دیگر (Mac, Linux) می‌توانند از طریق HTTP به این سرویس درخواست ارسال کنند.

## 🔧 نصب روی سیستم ویندوزی

### 1. نصب Python و Dependencies

```bash
# نصب Python 3.8 یا بالاتر
# دانلود از: https://www.python.org/downloads/

# نصب dependencies
pip install -r requirements/bridge.txt
```

### 2. کپی فایل‌های لازم

فایل‌های زیر را به سیستم ویندوزی کپی کنید:
- `pos_bridge_service.py`
- `pna.pcpos.dll`
- `requirements/bridge.txt`

### 3. تنظیمات Environment Variables

یک فایل `.env` در همان پوشه `pos_bridge_service.py` ایجاد کنید:

```env
# Bridge Service Configuration
POS_BRIDGE_HOST=0.0.0.0  # برای دسترسی از شبکه (یا 127.0.0.1 برای فقط localhost)
POS_BRIDGE_PORT=8080

# DLL Configuration
POS_DLL_PATH=pna.pcpos.dll  # مسیر DLL (می‌تواند absolute path باشد)

# POS Device Configuration
POS_TCP_HOST=192.168.20.151  # IP دستگاه POS
POS_TCP_PORT=1362            # Port دستگاه POS

# POS Terminal Configuration
POS_TERMINAL_ID=30739260
POS_MERCHANT_ID=300000001235935
POS_DEVICE_SERIAL=54040919
```

### 4. اجرای سرویس

```bash
python pos_bridge_service.py
```

سرویس روی `http://0.0.0.0:8080` اجرا می‌شود.

## 🔧 تنظیمات روی سیستم اصلی (Mac/Linux)

### 1. تنظیمات .env

در فایل `.env` سیستم اصلی:

```env
# استفاده از Bridge Service
POS_USE_BRIDGE=True

# آدرس سیستم ویندوزی
POS_BRIDGE_HOST=192.168.1.50  # IP سیستم ویندوزی
POS_BRIDGE_PORT=8080
```

### 2. تست اتصال

```bash
# تست اتصال به bridge service
curl http://192.168.1.50:8080/health

# تست اتصال به POS
curl -X POST http://192.168.1.50:8080/test-connection
```

## 📡 API Endpoints

### GET /health
بررسی سلامت سرویس

**Response:**
```json
{
  "status": "ok",
  "dll_available": true,
  "pos_initialized": true,
  "service": "POS Bridge Service"
}
```

### POST /test-connection
تست اتصال به دستگاه POS

**Response:**
```json
{
  "success": true,
  "message": "Connection test completed",
  "connected": true
}
```

### POST /payment
ارسال تراکنش پرداخت

**Request:**
```json
{
  "amount": 10000,
  "order_number": "ORDER-001",
  "customer_name": "John Doe",
  "payment_id": "PAY123",
  "bill_id": "BILL456"
}
```

**Response:**
```json
{
  "success": true,
  "transaction_id": "POS-1234567890-10000",
  "status": "success",
  "response_code": "00",
  "response_message": "Transaction successful",
  "reference_number": "123456789012",
  "card_number": "1234****5678",
  "amount": 10000
}
```

## 🔒 امنیت

برای استفاده در محیط production:

1. **فایروال**: فقط IP های مجاز را اجازه دهید
2. **HTTPS**: از reverse proxy (nginx) با SSL استفاده کنید
3. **Authentication**: API key یا token اضافه کنید
4. **Rate Limiting**: محدودیت تعداد درخواست اضافه کنید

## 🐛 عیب‌یابی

### مشکل: سرویس شروع نمی‌شود
- بررسی کنید که Python و dependencies نصب شده‌اند
- بررسی کنید که DLL در مسیر درست است
- لاگ‌ها را بررسی کنید

### مشکل: اتصال به POS برقرار نمی‌شود
- بررسی کنید که IP و Port درست است
- بررسی کنید که Terminal ID و Merchant ID درست است
- بررسی کنید که دستگاه POS روشن است و به شبکه متصل است

### مشکل: سیستم اصلی نمی‌تواند به bridge وصل شود
- بررسی کنید که firewall ویندوز اجازه می‌دهد
- بررسی کنید که IP و Port درست است
- بررسی کنید که سرویس در حال اجرا است

## 📝 مثال استفاده

### از Python:
```python
import requests

response = requests.post(
    'http://192.168.1.50:8080/payment',
    json={
        'amount': 10000,
        'order_number': 'ORDER-001'
    },
    timeout=130
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Reference Number: {result['reference_number']}")
```

### از curl:
```bash
curl -X POST http://192.168.1.50:8080/payment \
     -H "Content-Type: application/json" \
     -d '{
       "amount": 10000,
       "order_number": "ORDER-001"
     }'
```

## 🚀 اجرای خودکار (Windows Service)

برای اجرای خودکار سرویس در Windows:

1. استفاده از `nssm` (Non-Sucking Service Manager):
```bash
nssm install POSBridgeService "C:\Python\python.exe" "C:\path\to\pos_bridge_service.py"
nssm start POSBridgeService
```

2. یا استفاده از Task Scheduler برای اجرا در startup

## ✅ مزایا

- ✅ پشتیبانی از تمام پلتفرم‌ها (Mac, Linux, Windows)
- ✅ استفاده از DLL اصلی (بدون نیاز به reverse engineering)
- ✅ مدیریت متمرکز اتصال POS
- ✅ لاگ‌گیری و عیب‌یابی بهتر
- ✅ امکان استفاده از چند سیستم همزمان

