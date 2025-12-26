# راهنمای Docker برای پروژه کیوسک

## پیش‌نیازها

- Docker Engine 20.10+
- Docker Compose 2.0+

## دو مدل Docker

این پروژه دو مدل Docker دارد:
- **Development**: برای توسعه و تست
- **Production**: برای محیط Production

---

## Development Mode

### راه‌اندازی سریع

#### 1. کپی کردن فایل Environment

```bash
cp .env.example .env
```

سپس فایل `.env` را ویرایش کنید و مقادیر مورد نیاز را تنظیم کنید.

**نکته مهم**: برای استفاده با Docker، `DATABASE_HOST` را به `db` تغییر دهید.

#### 2. ساخت و راه‌اندازی Containers

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

یا با Makefile:
```bash
make build-dev
make up-dev
```

#### 3. ایجاد Superuser

```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

یا:
```bash
make createsuperuser-dev
```

#### 4. دسترسی به پروژه

- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/

### ویژگی‌های Development Mode

- استفاده از Django `runserver`
- Volume mount برای کد (تغییرات فوری اعمال می‌شود)
- Debug Toolbar فعال
- Logs در Console
- Hot reload

---

## Production Mode

### راه‌اندازی

#### 1. تنظیم Environment Variables

مطمئن شوید که فایل `.env` برای Production تنظیم شده است:
- `DEBUG=False`
- `ALLOWED_HOSTS` شامل domain شما
- `SECRET_KEY` قوی و امن
- Database credentials صحیح

#### 2. ساخت و راه‌اندازی Containers

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

یا با Makefile:
```bash
make build-prod
make up-prod
```

#### 3. ایجاد Superuser

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

یا:
```bash
make createsuperuser-prod
```

### ویژگی‌های Production Mode

- استفاده از Gunicorn با 4 workers
- Static files جمع‌آوری شده
- Security settings فعال
- Read-only containers
- Restart policy: always
- بدون volume mount برای کد

## دستورات مفید

### Development

#### مشاهده Logs
```bash
docker-compose -f docker-compose.dev.yml logs -f web
make logs-dev
```

#### اجرای Migrations
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
make migrate-dev
```

#### ساخت Migrations جدید
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations
make makemigrations-dev
```

#### دسترسی به Shell Django
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py shell
make shell-dev
```

#### دسترسی به Shell Container
```bash
docker-compose -f docker-compose.dev.yml exec web bash
```

#### توقف Containers
```bash
docker-compose -f docker-compose.dev.yml down
make down-dev
```

### Production

#### مشاهده Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f web
make logs-prod
```

#### اجرای Migrations
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
make migrate-prod
```

#### توقف Containers
```bash
docker-compose -f docker-compose.prod.yml down
make down-prod
```

## استفاده از Makefile

برای راحتی بیشتر، می‌توانید از Makefile استفاده کنید:

### Development Commands
```bash
make build-dev          # ساخت development images
make up-dev             # راه‌اندازی development containers
make down-dev           # توقف development containers
make logs-dev           # مشاهده logs
make shell-dev          # دسترسی به Django shell
make migrate-dev        # اجرای migrations
make createsuperuser-dev # ایجاد superuser
make test-dev           # اجرای tests
make clean-dev          # حذف containers و volumes
```

### Production Commands
```bash
make build-prod         # ساخت production images
make up-prod            # راه‌اندازی production containers
make down-prod          # توقف production containers
make logs-prod          # مشاهده logs
make migrate-prod       # اجرای migrations
make createsuperuser-prod # ایجاد superuser
make clean-prod         # حذف containers و volumes
```

### Default Commands (Development)
```bash
make build              # همان build-dev
make up                 # همان up-dev
make down               # همان down-dev
make logs               # همان logs-dev
make shell              # همان shell-dev
make migrate            # همان migrate-dev
make createsuperuser    # همان createsuperuser-dev
make test               # همان test-dev
make clean              # همان clean-dev
```

برای مشاهده تمام دستورات:
```bash
make help
```

## Troubleshooting

### مشکل اتصال Database

```bash
docker-compose exec db psql -U kiosk_user -d kiosk_db
```

### بررسی وضعیت Containers

```bash
docker-compose ps
```

### مشاهده Logs کامل

```bash
docker-compose logs --tail=100 web
```

### Reset Database (Development)

```bash
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

یا:
```bash
make clean-dev
make up-dev
make migrate-dev
make createsuperuser-dev
```

## Health Check Endpoints

پروژه دارای سه endpoint برای health check است:

### 1. Health Check (کامل)
```bash
curl http://localhost:8000/health/
```

بررسی اتصال Database و وضعیت کلی سیستم.

**Response (Healthy):**
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "kiosk_backend"
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "...",
  "service": "kiosk_backend"
}
```

### 2. Readiness Check
```bash
curl http://localhost:8000/health/ready/
```

بررسی آماده بودن سرویس برای دریافت ترافیک.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "service": true
  },
  "service": "kiosk_backend"
}
```

### 3. Liveness Check
```bash
curl http://localhost:8000/health/live/
```

بررسی زنده بودن سرویس (بدون بررسی Database).

**Response:**
```json
{
  "status": "alive",
  "service": "kiosk_backend"
}
```

### استفاده در Docker

Docker به صورت خودکار از `/health/` برای health check استفاده می‌کند. می‌توانید وضعیت را بررسی کنید:

```bash
docker-compose -f docker-compose.dev.yml ps
```

یا:
```bash
docker ps
```

## استفاده از Makefile

**Makefile** یک فایل متنی است که دستورات shell را به صورت ساده و قابل استفاده تبدیل می‌کند. به جای تایپ کردن دستورات طولانی Docker، می‌توانید از دستورات کوتاه استفاده کنید.

### مزایای استفاده از Makefile

1. **سادگی**: دستورات کوتاه و قابل فهم
2. **یکنواختی**: همه از یک دستورات استفاده می‌کنند
3. **مستندسازی**: خود فایل Makefile یک مستند است
4. **خطای کمتر**: کمتر احتمال تایپ اشتباه

### مثال

**بدون Makefile:**
```bash
docker-compose -f docker-compose.dev.yml up -d --build
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

**با Makefile:**
```bash
make up-dev
make migrate-dev
```

### دستورات Development

```bash
make build-dev          # ساخت Docker images
make up-dev            # راه‌اندازی containers
make down-dev          # توقف containers
make restart-dev       # Restart containers
make logs-dev          # مشاهده logs
make shell-dev         # دسترسی به Django shell
make migrate-dev       # اجرای migrations
make makemigrations-dev # ساخت migrations جدید
make createsuperuser-dev # ایجاد superuser
make test-dev          # اجرای tests
make clean-dev         # حذف containers و volumes
```

### دستورات Production

```bash
make build-prod        # ساخت Docker images
make up-prod           # راه‌اندازی containers
make down-prod         # توقف containers
make restart-prod      # Restart containers
make logs-prod         # مشاهده logs
make migrate-prod      # اجرای migrations
make createsuperuser-prod # ایجاد superuser
make clean-prod        # حذف containers و volumes
```

### Default Commands (Development)

```bash
make build             # همان build-dev
make up                # همان up-dev
make down              # همان down-dev
make logs              # همان logs-dev
make shell             # همان shell-dev
make migrate           # همان migrate-dev
make createsuperuser   # همان createsuperuser-dev
make test              # همان test-dev
make clean             # همان clean-dev
```

### مشاهده تمام دستورات

```bash
make help
```

### مثال Workflow کامل

```bash
# 1. ساخت images
make build-dev

# 2. راه‌اندازی
make up-dev

# 3. اجرای migrations
make migrate-dev

# 4. ایجاد superuser
make createsuperuser-dev

# 5. مشاهده logs
make logs-dev

# 6. دسترسی به shell
make shell-dev

# 7. توقف
make down-dev
```

