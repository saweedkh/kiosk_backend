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
- ✅ سیستم Backup خودکار
- ✅ تنظیمات Gateway پرداخت

### ویژگی‌های فنی
- ✅ Session-based Authentication برای کیوسک
- ✅ Django Session Authentication برای ادمین
- ✅ مدیریت موجودی با تاریخچه تغییرات
- ✅ لاگ کامل تمام تراکنش‌ها و عملیات
- ✅ Backup خودکار روزانه و Incremental
- ✅ تولید فاکتور PDF
- ✅ API Documentation با Swagger/OpenAPI

---

## تکنولوژی‌ها

### Backend
- **Django 4.2+**: Framework اصلی
- **Django REST Framework**: برای API
- **PostgreSQL**: Database
- **Celery**: برای Background Tasks
- **Redis**: برای Celery Broker
- **ReportLab**: برای تولید PDF

### Tools
- **django-cors-headers**: برای CORS
- **django-filter**: برای Filtering
- **drf-spectacular**: برای API Documentation (اختیاری)

---

## نیازمندی‌ها

### نرم‌افزار
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Virtual Environment (venv یا virtualenv)

### Python Packages
تمام پکیج‌های مورد نیاز در `requirements/` تعریف شده‌اند.

---

## نصب و راه‌اندازی

### 1. Clone پروژه
```bash
git clone <repository-url>
cd kiosk
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
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_NAME=kiosk_db
DATABASE_USER=kiosk_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
REDIS_URL=redis://localhost:6379/0
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

### 9. راه‌اندازی Redis
```bash
redis-server
```

### 10. راه‌اندازی Celery Worker
```bash
celery -A config worker -l info
```

### 11. راه‌اندازی Celery Beat (برای Scheduled Tasks)
```bash
celery -A config beat -l info
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
برای تنظیم Gateway پرداخت:
1. از پنل ادمین به بخش Gateway Config بروید
2. یا از API استفاده کنید: `POST /api/admin/payment/gateway/`

### Backup Settings
در `apps/core/backup/manager.py` می‌توانید تنظیمات Backup را تغییر دهید:
- فاصله زمانی Backup
- تعداد Backup های نگهداری شده
- مسیر ذخیره‌سازی

---

## اجرای پروژه

### Development Mode
```bash
python manage.py runserver
```

پروژه در `http://localhost:8000` اجرا می‌شود.

### API Documentation
بعد از راه‌اندازی، به آدرس زیر بروید:
```
http://localhost:8000/api/docs/
```

### Admin Panel
```
http://localhost:8000/admin/
```

---

## API Documentation

مستندات کامل API در [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) موجود است.

### Base URLs
- **Kiosk APIs**: `/api/kiosk/`
- **Admin APIs**: `/api/admin/`

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

### Celery در Production
```bash
# Worker
celery -A config worker --loglevel=info --detach

# Beat
celery -A config beat --loglevel=info --detach
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

[program:celery_worker]
command=/path/to/venv/bin/celery -A config worker --loglevel=info
directory=/path/to/kiosk
user=www-data
autostart=true
autorestart=true

[program:celery_beat]
command=/path/to/venv/bin/celery -A config beat --loglevel=info
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

### مشکل Celery
- بررسی کنید Redis در حال اجرا باشد
- بررسی کنید `REDIS_URL` در `.env` درست باشد

---

## Contributing

1. Fork پروژه
2. ایجاد Branch (`git checkout -b feature/AmazingFeature`)
3. Commit تغییرات (`git commit -m 'Add some AmazingFeature'`)
4. Push به Branch (`git push origin feature/AmazingFeature`)
5. ایجاد Pull Request

---

## License

این پروژه تحت مجوز MIT منتشر شده است.

---

## Support

برای پشتیبانی و سوالات:
- ایجاد Issue در Repository
- تماس با تیم توسعه

---

## Changelog

### Version 1.0.0
- پیاده‌سازی کامل سیستم
- Products Module
- Cart Module
- Orders Module
- Payment Module (Mock Gateway)
- Logs Module
- Admin Panel
- Backup System

---

**موفق باشید! 🚀**

