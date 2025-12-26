# مستندات API پروژه کیوسک

## 📋 فهرست مطالب
1. [Authentication](#authentication)
2. [Kiosk APIs](#kiosk-apis)
3. [Admin APIs](#admin-apis)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)

---

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

---

## Authentication

### Kiosk APIs
Kiosk APIs از Session-based Authentication استفاده می‌کنند. Session به صورت خودکار ایجاد می‌شود.

### Admin APIs
Admin APIs از Django Session Authentication استفاده می‌کنند.

---

## Kiosk APIs

### Base Path: `/api/kiosk/`

---

### Products API

#### لیست محصولات
```http
GET /api/kiosk/products/
```

**Query Parameters:**
- `category` (int, optional): فیلتر بر اساس دسته‌بندی
- `min_price` (int, optional): حداقل قیمت
- `max_price` (int, optional): حداکثر قیمت
- `in_stock` (bool, optional): فقط محصولات موجود
- `search` (string, optional): جستجو در نام و توضیحات

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/kiosk/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "محصول نمونه",
      "description": "توضیحات محصول",
      "price": 100000,
      "category": 1,
      "category_name": "دسته‌بندی",
      "image": "http://localhost:8000/media/products/image.jpg",
      "stock_quantity": 50,
      "is_active": true
    }
  ]
}
```

#### جزئیات محصول
```http
GET /api/kiosk/products/{id}/
```

**Response:**
```json
{
  "id": 1,
  "name": "محصول نمونه",
  "description": "توضیحات کامل محصول",
  "price": 100000,
  "category": 1,
  "category_name": "دسته‌بندی",
  "image": "http://localhost:8000/media/products/image.jpg",
  "stock_quantity": 50,
  "is_active": true
}
```

#### جستجوی محصولات
```http
GET /api/kiosk/products/search/?q=query
```

**Response:** همانند لیست محصولات

---

### Categories API

#### لیست دسته‌بندی‌ها
```http
GET /api/kiosk/categories/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "دسته‌بندی اصلی",
    "parent": null,
    "display_order": 1,
    "is_active": true
  }
]
```

#### محصولات یک دسته‌بندی
```http
GET /api/kiosk/categories/{id}/products/
```

**Response:** لیست محصولات همانند Products API

---

### Cart API

#### دریافت سبد خرید فعلی
```http
GET /api/kiosk/cart/current/
```

**Response:**
```json
{
  "id": 1,
  "session_key": "abc123",
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "محصول نمونه",
        "price": 100000
      },
      "quantity": 2,
      "unit_price": 100000,
      "subtotal": 200000
    }
  ],
  "total": 200000,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### دریافت مجموع سبد خرید
```http
GET /api/kiosk/cart/total/
```

**Response:**
```json
{
  "total": 200000
}
```

#### پاک کردن سبد خرید
```http
DELETE /api/kiosk/cart/clear/
```

**Response:** `204 No Content`

---

### Cart Items API

#### افزودن محصول به سبد
```http
POST /api/kiosk/cart-items/
```

**Request Body:**
```json
{
  "product_id": 1,
  "quantity": 2
}
```

**Response:**
```json
{
  "id": 1,
  "product": {
    "id": 1,
    "name": "محصول نمونه",
    "price": 100000
  },
  "quantity": 2,
  "unit_price": 100000,
  "subtotal": 200000
}
```

#### تغییر تعداد محصول در سبد
```http
PUT /api/kiosk/cart-items/{id}/
PATCH /api/kiosk/cart-items/{id}/
```

**Request Body:**
```json
{
  "quantity": 3
}
```

**Response:** همانند افزودن محصول

#### حذف محصول از سبد
```http
DELETE /api/kiosk/cart-items/{id}/
```

**Response:** `204 No Content`

---

### Payment API

#### شروع پرداخت
```http
POST /api/kiosk/payment/initiate/
```

**Request Body:**
```json
{
  "cart_id": 1,
  "amount": 200000
}
```

**Response:**
```json
{
  "transaction_id": "txn_123456",
  "status": "pending",
  "gateway_url": "https://gateway.com/pay/txn_123456"
}
```

#### تایید پرداخت
```http
POST /api/kiosk/payment/verify/
```

**Request Body:**
```json
{
  "transaction_id": "txn_123456"
}
```

**Response:**
```json
{
  "status": "success",
  "order_number": "ORD-2024-001",
  "message": "پرداخت با موفقیت انجام شد"
}
```

#### وضعیت پرداخت
```http
GET /api/kiosk/payment/status/?transaction_id=txn_123456
```

**Response:**
```json
{
  "transaction_id": "txn_123456",
  "status": "success",
  "amount": 200000,
  "order_number": "ORD-2024-001"
}
```

---

### Orders API

#### دریافت سفارش
```http
GET /api/kiosk/orders/{order_number}/
```

**Response:**
```json
{
  "id": 1,
  "order_number": "ORD-2024-001",
  "total_amount": 200000,
  "payment_status": "paid",
  "items": [
    {
      "id": 1,
      "product_name": "محصول نمونه",
      "quantity": 2,
      "unit_price": 100000,
      "subtotal": 200000
    }
  ],
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### دانلود فاکتور PDF
```http
GET /api/kiosk/orders/{order_number}/invoice/
```

**Response:** فایل PDF

#### دریافت فاکتور JSON
```http
GET /api/kiosk/orders/{order_number}/invoice/json/
```

**Response:**
```json
{
  "invoice_number": "INV-2024-001",
  "order_number": "ORD-2024-001",
  "date": "2024-01-01",
  "items": [
    {
      "product_name": "محصول نمونه",
      "quantity": 2,
      "unit_price": 100000,
      "subtotal": 200000
    }
  ],
  "total": 200000,
  "payment_method": "کارت خوان",
  "transaction_id": "txn_123456"
}
```

---

## Admin APIs

### Base Path: `/api/admin/`

---

### Authentication API

#### لاگین
```http
POST /api/admin/auth/login/
```

**Request Body:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User"
  },
  "message": "Login successful"
}
```

#### خروج
```http
POST /api/admin/auth/logout/
```

**Headers:**
```
Authorization: Session <session_id>
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

#### اطلاعات کاربر لاگین شده
```http
GET /api/admin/auth/me/
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User"
}
```

---

### Products Management API

#### لیست محصولات
```http
GET /api/admin/products/
```

**Query Parameters:**
- `page` (int): شماره صفحه
- `page_size` (int): تعداد در هر صفحه
- `category` (int): فیلتر بر اساس دسته‌بندی
- `is_active` (bool): فیلتر بر اساس وضعیت
- `search` (string): جستجو

**Response:** همانند Products API (با pagination)

#### افزودن محصول
```http
POST /api/admin/products/
```

**Request Body:**
```json
{
  "name": "محصول جدید",
  "description": "توضیحات",
  "price": 100000,
  "category": 1,
  "stock_quantity": 50,
  "min_stock_level": 10,
  "is_active": true
}
```

**Response:** جزئیات محصول

#### ویرایش محصول
```http
PUT /api/admin/products/{id}/
PATCH /api/admin/products/{id}/
```

**Request Body:** همانند افزودن محصول

#### تغییر موجودی
```http
PUT /api/admin/products/{id}/update_stock/
```

**Request Body:**
```json
{
  "quantity": 100
}
```

**Response:** جزئیات محصول به‌روز شده

#### حذف محصول
```http
DELETE /api/admin/products/{id}/
```

**Response:** `204 No Content`

---

### Categories Management API

#### لیست دسته‌بندی‌ها
```http
GET /api/admin/categories/
```

**Response:** همانند Categories API

#### افزودن دسته‌بندی
```http
POST /api/admin/categories/
```

**Request Body:**
```json
{
  "name": "دسته‌بندی جدید",
  "parent": null,
  "display_order": 1,
  "is_active": true
}
```

#### ویرایش دسته‌بندی
```http
PUT /api/admin/categories/{id}/
PATCH /api/admin/categories/{id}/
```

#### حذف دسته‌بندی
```http
DELETE /api/admin/categories/{id}/
```

---

### Orders Management API

#### لیست سفارشات
```http
GET /api/admin/orders/
```

**Query Parameters:**
- `page` (int): شماره صفحه
- `payment_status` (string): فیلتر بر اساس وضعیت پرداخت
- `start_date` (date): تاریخ شروع
- `end_date` (date): تاریخ پایان
- `order_number` (string): جستجو بر اساس شماره سفارش

**Response:**
```json
{
  "count": 50,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "order_number": "ORD-2024-001",
      "total_amount": 200000,
      "payment_status": "paid",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### جزئیات سفارش
```http
GET /api/admin/orders/{id}/
```

**Response:** جزئیات کامل سفارش

---

### Reports API

#### گزارش فروش
```http
GET /api/admin/reports/sales/
```

**Query Parameters:**
- `start_date` (date, required): تاریخ شروع
- `end_date` (date, required): تاریخ پایان

**Response:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "total_sales": 5000000,
  "order_count": 25,
  "average_order": 200000,
  "daily_breakdown": [
    {
      "date": "2024-01-01",
      "sales": 200000,
      "orders": 2
    }
  ]
}
```

#### گزارش فروش PDF
```http
GET /api/admin/reports/sales/pdf/?start_date=2024-01-01&end_date=2024-01-31
```

**Response:** فایل PDF

#### گزارش تراکنش‌ها
```http
GET /api/admin/reports/transactions/
```

**Query Parameters:**
- `start_date` (date, required)
- `end_date` (date, required)

**Response:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "total_amount": 5000000,
  "success_count": 24,
  "failed_count": 1,
  "total_count": 25,
  "success_rate": 96.0
}
```

#### گزارش محصولات
```http
GET /api/admin/reports/products/
```

**Query Parameters:**
- `start_date` (date, optional)
- `end_date` (date, optional)
- `limit` (int, optional): تعداد محصولات برتر (default: 10)

**Response:**
```json
{
  "top_products": [
    {
      "product_name": "محصول نمونه",
      "total_sold": 50,
      "total_revenue": 5000000
    }
  ]
}
```

#### گزارش موجودی
```http
GET /api/admin/reports/stocks/
```

**Response:**
```json
{
  "total_products": 100,
  "active_products": 80,
  "low_stock": 10,
  "out_of_stock": 5,
  "low_stock_products": [
    {
      "id": 1,
      "name": "محصول نمونه",
      "stock_quantity": 5,
      "min_stock_level": 10
    }
  ]
}
```

---

### Backups API

#### لیست Backup ها
```http
GET /api/admin/backups/
```

**Response:**
```json
[
  {
    "id": 1,
    "backup_type": "full",
    "file_path": "/media/backups/backup_2024-01-01.sql",
    "file_size": 1048576,
    "status": "completed",
    "started_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:05:00Z"
  }
]
```

#### ایجاد Backup دستی
```http
POST /api/admin/backups/create/
```

**Request Body:**
```json
{
  "backup_type": "full"
}
```

**Response:**
```json
{
  "id": 1,
  "status": "pending",
  "message": "Backup started"
}
```

#### دانلود Backup
```http
GET /api/admin/backups/{id}/download/
```

**Response:** فایل Backup

#### حذف Backup
```http
DELETE /api/admin/backups/{id}/
```

**Response:** `204 No Content`

---

### Logs API

#### لیست لاگ‌های سیستم
```http
GET /api/admin/logs/system/
```

**Query Parameters:**
- `log_type` (string): نوع لاگ (transaction, order, payment, product, admin_action)
- `level` (string): سطح لاگ (info, warning, error, critical)
- `start_date` (date): تاریخ شروع
- `end_date` (date): تاریخ پایان

**Response:**
```json
{
  "count": 1000,
  "results": [
    {
      "id": 1,
      "log_type": "order",
      "level": "info",
      "action": "order_created",
      "details": {
        "order_number": "ORD-2024-001",
        "total_amount": 200000
      },
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### لاگ‌های تراکنش
```http
GET /api/admin/logs/transactions/
```

**Query Parameters:**
- `transaction_id` (string): فیلتر بر اساس transaction_id
- `start_date` (date): تاریخ شروع
- `end_date` (date): تاریخ پایان

**Response:** لیست لاگ‌های تراکنش

---

## Error Handling

### Error Response Format
```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes
- `200 OK`: درخواست موفق
- `201 Created`: ایجاد موفق
- `204 No Content`: حذف موفق
- `400 Bad Request`: درخواست نامعتبر
- `401 Unauthorized`: نیاز به احراز هویت
- `403 Forbidden`: دسترسی غیرمجاز
- `404 Not Found`: یافت نشد
- `500 Internal Server Error`: خطای سرور

### مثال Error Response
```json
{
  "error": "Product not found",
  "detail": "Product with id 999 does not exist",
  "code": "PRODUCT_NOT_FOUND"
}
```

---

## Rate Limiting

- Kiosk APIs: 100 requests per minute
- Admin APIs: 200 requests per minute
- Payment APIs: 10 requests per minute

---

## Pagination

تمام API های لیست از Pagination استفاده می‌کنند:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/kiosk/products/?page=2",
  "previous": null,
  "results": [...]
}
```

**Query Parameters:**
- `page` (int): شماره صفحه (default: 1)
- `page_size` (int): تعداد در هر صفحه (default: 20, max: 100)

---

## Notes

- تمام تاریخ‌ها به فرمت ISO 8601 هستند: `YYYY-MM-DDTHH:MM:SSZ`
- تمام مبالغ به ریال هستند
- تمام API ها از JSON استفاده می‌کنند
- برای Admin APIs نیاز به Authentication است

