# پروژه کیوسک - سیستم فروشگاهی با پرداخت کارت‌خوان

سیستم مدیریت فروشگاه برای دستگاه‌های کیوسک با قابلیت اتصال به کارت‌خوان و مدیریت کامل محصولات، سفارشات و گزارش‌گیری.

## 📋 فهرست مطالب

- [ویژگی‌ها](#ویژگی‌ها)
- [تکنولوژی‌ها](#تکنولوژی‌ها)
- [نیازمندی‌ها](#نیازمندی‌ها)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [ساختار پروژه](#ساختار-پروژه)
- [تنظیمات](#تنظیمات)
- [اجرای پروژه](#اجرای-پروژه)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)

---

## ویژگی‌ها

### برای دستگاه کیوسک
- ✅ نمایش منوی محصولات و دسته‌بندی‌ها
- ✅ مدیریت سبد خرید (افزودن، ویرایش، حذف)
- ✅ پرداخت از طریق کارت‌خوان
- ✅ ثبت سفارش و تولید فاکتور (PDF + JSON)
- ✅ دانلود فاکتور

### برای پنل ادمین
- ✅ مدیریت محصولات و دسته‌بندی‌ها
- ✅ مدیریت موجودی محصولات
- ✅ مشاهده و مدیریت سفارشات
- ✅ گزارش‌گیری کامل (فروش، تراکنش‌ها، محصولات، موجودی)
- ✅ مدیریت لاگ‌های سیستم و تراکنش‌ها
- ✅ تنظیمات Gateway پرداخت (از طریق Environment Variables)

### ویژگی‌های فنی
- ✅ Session-based Authentication برای کیوسک
- ✅ Django Session Authentication برای ادمین
- ✅ مدیریت موجودی با تاریخچه تغییرات
- ✅ لاگ کامل تمام تراکنش‌ها و عملیات (Console و File-based)
- ✅ تولید فاکتور PDF و JSON
- ✅ معماری Layered (API, Service, Selector, Model)
- ✅ Modular API Structure

---

## تکنولوژی‌ها

### Backend
- **Django 4.2.16**: Framework اصلی
- **Django REST Framework 3.15.2**: برای API
- **PostgreSQL**: Database
- **ReportLab 4.2.5**: برای تولید PDF

### Tools
- **django-cors-headers 4.6.0**: برای CORS
- **django-filter 24.3**: برای Filtering
- **python-dotenv 1.0.1**: برای مدیریت Environment Variables
- **Pillow 10.4.0**: برای پردازش تصاویر

---

## نیازمندی‌ها

### نرم‌افزار
- Python 3.9+
- PostgreSQL 12+
- Virtual Environment (venv یا virtualenv)

### Python Packages
تمام پکیج‌های مورد نیاز در `requirements/` تعریف شده‌اند.

---

## نصب و راه‌اندازی

### 1. Clone پروژه
```bash
git clone https://github.com/saweedkh/kiosk_backend.git
cd kiosk_backend
```

### 2. ایجاد Virtual Environment
```bash
python3.9 -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate  # Windows
```

### 3. نصب Dependencies
```bash
pip install -r requirements/base.txt
pip install -r requirements/development.txt
```

### 4. تنظیم Database

#### ایجاد Database در PostgreSQL
```sql
CREATE DATABASE kiosk_db;
CREATE USER kiosk_user WITH PASSWORD 'your_password';
ALTER ROLE kiosk_user SET client_encoding TO 'utf8';
ALTER ROLE kiosk_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE kiosk_user SET timezone TO 'Asia/Tehran';
GRANT ALL PRIVILEGES ON DATABASE kiosk_db TO kiosk_user;
```

### 5. تنظیم Environment Variables

کپی کردن `.env.example` به `.env`:
```bash
cp .env.example .env
```

ویرایش `.env`:
```env
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_NAME=kiosk_db
DATABASE_USER=kiosk_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

PAYMENT_GATEWAY_NAME=mock
PAYMENT_GATEWAY_ACTIVE=True
PAYMENT_GATEWAY_API_KEY=mock_api_key_123
PAYMENT_GATEWAY_API_SECRET=mock_api_secret_abc
PAYMENT_GATEWAY_MERCHANT_ID=mock_merchant_id_xyz
PAYMENT_GATEWAY_TERMINAL_ID=mock_terminal_id_789
PAYMENT_GATEWAY_CALLBACK_URL=http://localhost:8000/api/kiosk/payment/verify/
```

### 6. اجرای Migrations
```bash
python manage.py migrate
```

### 7. ایجاد Superuser
```bash
python manage.py createsuperuser
```

### 8. جمع‌آوری Static Files
```bash
python manage.py collectstatic --noinput
```

---

## ساختار پروژه

```
kiosk/
├── config/                 # Project Configuration
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/                   # Django Apps
│   ├── products/          # Products Module
│   ├── cart/              # Cart Module
│   ├── orders/            # Orders Module
│   ├── payment/           # Payment Module
│   ├── logs/               # Logs Module
│   ├── admin_panel/        # Admin Panel
│   └── core/               # Core Utilities
│
├── static/                 # Static Files
├── media/                  # Media Files
├── logs/                   # Application Logs
├── requirements/           # Python Dependencies
├── docs/                   # Documentation
└── tests/                  # Integration Tests
```

برای جزئیات بیشتر ساختار، به [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) مراجعه کنید.

---

## تنظیمات

### Database Settings
در `config/settings/base.py` یا `.env` تنظیم کنید.

### Payment Gateway
برای تنظیم Gateway پرداخت، مقادیر را در فایل `.env` تنظیم کنید:
- `PAYMENT_GATEWAY_NAME`: نام Gateway (مثلاً `mock`)
- `PAYMENT_GATEWAY_ACTIVE`: فعال/غیرفعال بودن Gateway
- `PAYMENT_GATEWAY_API_KEY`: کلید API
- `PAYMENT_GATEWAY_API_SECRET`: Secret Key
- `PAYMENT_GATEWAY_MERCHANT_ID`: شناسه Merchant
- `PAYMENT_GATEWAY_TERMINAL_ID`: شناسه Terminal
- `PAYMENT_GATEWAY_CALLBACK_URL`: URL برای Callback

---

## اجرای پروژه

### Development Mode
```bash
python manage.py runserver
```

پروژه در `http://localhost:8000` اجرا می‌شود.

### API Documentation
مستندات کامل API در فایل [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) موجود است.

### Admin Panel
```
http://localhost:8000/admin/
```

---

## API Documentation

مستندات کامل API در [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) موجود است.

### Base URLs
- **Kiosk APIs**: `/api/kiosk/`
- **Admin APIs**: `/api/kiosk/admin-panel/`

### مثال استفاده

#### دریافت لیست محصولات
```bash
curl http://localhost:8000/api/kiosk/products/
```

#### افزودن محصول به سبد
```bash
curl -X POST http://localhost:8000/api/kiosk/cart-items/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'
```

---

## Testing

### اجرای تمام Tests
```bash
python manage.py test
```

### اجرای Tests یک App خاص
```bash
python manage.py test apps.products
```

### اجرای یک Test خاص
```bash
python manage.py test apps.products.tests.test_models.TestProductModel
```

### با Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## Deployment

### Production Settings

1. تغییر `DEBUG = False` در `config/settings/production.py`
2. تنظیم `ALLOWED_HOSTS`
3. تنظیم `SECRET_KEY` در `.env`
4. تنظیم Static Files و Media Files
5. تنظیم SSL Certificate

### با Gunicorn
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### با Nginx
مثال Configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/static/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

### با Supervisor
مثال Configuration:
```ini
[program:kiosk]
command=/path/to/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000
directory=/path/to/kiosk
user=www-data
autostart=true
autorestart=true
```

---

## نقشه راه پیاده‌سازی

برای مشاهده نقشه راه کامل پیاده‌سازی، به [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) مراجعه کنید.

---

## Troubleshooting

### مشکل اتصال Database
- بررسی کنید PostgreSQL در حال اجرا باشد
- بررسی کنید Credentials در `.env` درست باشد
- بررسی کنید Database ایجاد شده باشد

### مشکل Static Files
```bash
python manage.py collectstatic --noinput
```

### مشکل Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Contributing

1. Fork پروژه از [GitHub Repository](https://github.com/saweedkh/kiosk_backend)
2. Clone پروژه Fork شده
3. ایجاد Branch (`git checkout -b feature/AmazingFeature`)
4. Commit تغییرات (`git commit -m 'Add some AmazingFeature'`)
5. Push به Branch (`git push origin feature/AmazingFeature`)
6. ایجاد Pull Request در GitHub

---

## License

این پروژه تحت مجوز MIT منتشر شده است.

---

## Support

برای پشتیبانی و سوالات:
- ایجاد Issue در [GitHub Repository](https://github.com/saweedkh/kiosk_backend)
- تماس با تیم توسعه

---

## Changelog

### Version 1.0.0
- پیاده‌سازی کامل سیستم
- Products Module
- Cart Module
- Orders Module
- Payment Module (Mock Gateway)
- Logs Module (Console و File-based)
- Admin Panel
- Modular API Structure
- Layered Architecture

---

**موفق باشید! 🚀**

