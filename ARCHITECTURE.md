# معماری سیستم کیوسک

## 📋 فهرست مطالب
1. [معماری کلی](#معماری-کلی)
2. [Layered Architecture](#layered-architecture)
3. [ساختار هر App](#ساختار-هر-app)
4. [جریان داده](#جریان-داده)
5. [Database Schema](#database-schema)
6. [API Structure](#api-structure)
7. [Security](#security)

---

## معماری کلی

```
┌─────────────────────────────────────────┐
│         Frontend (Kiosk UI)             │
│    (React/Vue - Separate Project)       │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTP/REST API
                  │
┌─────────────────▼───────────────────────┐
│         API Gateway / Router            │
│         (Django URLs)                    │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌───▼────┐
│Product│   │  Cart   │   │Payment │
│  API  │   │   API   │   │  API   │
└───┬───┘   └────┬────┘   └───┬────┘
    │            │             │
┌───▼────────────▼─────────────▼───┐
│      API Layer (ViewSets)          │
│  (Serializers, Filters, Views)     │
└───┬───────────────────────────────┘
    │
┌───▼───────────────────────────────┐
│      Service Layer                 │
│  (Business Logic)                  │
└───┬───────────────────────────────┘
    │
┌───▼───────────────────────────────┐
│      Selector Layer                │
│  (Complex Queries)                │
└───┬───────────────────────────────┘
    │
┌───▼───────────────────────────────┐
│      Model Layer                   │
│  (Django ORM)                      │
└───┬───────────────────────────────┘
    │
┌───▼───────────────────────────────┐
│      Database (PostgreSQL)         │
└───────────────────────────────────┘
    │
┌───▼───────────────────────────────┐
│    External Payment Gateway        │
│    (Card Reader API/SDK)           │
└───────────────────────────────────┘
```

---

## Layered Architecture

### 1. API Layer
**مسئولیت:** Handling HTTP Requests/Responses

**Components:**
- ViewSets (Generic Views)
- Serializers (Data Validation & Serialization)
- Filters (Query Filtering)
- Permissions (Access Control)
- URLs (Routing)

**مثال:**
```python
# apps/products/api/products/products.py
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    
    def get_queryset(self):
        return ProductSelector.get_active_products()
```

### 2. Service Layer
**مسئولیت:** Business Logic

**Components:**
- Service Classes
- Business Rules
- Validation Logic
- Transaction Management

**مثال:**
```python
# apps/products/services/product_service.py
class ProductService:
    @staticmethod
    def create_product(validated_data):
        # Business Logic
        # Validation
        # Create Product
        return product
```

### 3. Selector Layer
**مسئولیت:** Complex Queries & Optimization

**Components:**
- Selector Classes
- Query Optimization (select_related, prefetch_related)
- Complex Filtering
- Aggregations

**مثال:**
```python
# apps/products/selectors/product_selector.py
class ProductSelector:
    @staticmethod
    def get_active_products():
        return Product.objects.active().select_related('category')
```

### 4. Model Layer
**مسئولیت:** Data Structure & Database Operations

**Components:**
- Django Models
- Custom Managers
- Model Methods
- Signals

**مثال:**
```python
# apps/products/models.py
class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    
    objects = ProductManager()
```

---

## ساختار هر App

```
app_name/
├── __init__.py
├── admin.py              # Django Admin
├── apps.py               # App Config
├── models.py             # Django Models
├── managers.py           # Custom Managers
├── signals.py            # Django Signals
├── validators.py         # Custom Validators
│
├── api/                  # API Layer
│   ├── __init__.py
│   ├── resource_name/    # هر API یک پوشه
│   │   ├── __init__.py
│   │   ├── resource_name.py  # ViewSet
│   │   ├── serializers.py   # Serializers
│   │   ├── filters.py       # Filters
│   │   └── urls.py          # URLs
│   └── urls.py          # Root URLs
│
├── selectors/            # Selector Layer
│   ├── __init__.py
│   └── selector_name.py
│
├── services/             # Service Layer
│   ├── __init__.py
│   └── service_name.py
│
├── utils/                # App-specific Utilities
│   └── helpers.py
│
└── tests/                # Tests
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_api.py
    └── factories.py
```

---

## جریان داده

### مثال: افزودن محصول به سبد

```
1. Frontend Request
   POST /api/kiosk/cart-items/
   Body: {"product_id": 1, "quantity": 2}
   ↓
2. URL Router
   apps/cart/api/cart_items/urls.py
   ↓
3. ViewSet
   apps/cart/api/cart_items/cart_items.py
   CartItemViewSet.create()
   ↓
4. Serializer Validation
   apps/cart/api/cart_items/serializers.py
   CartItemCreateSerializer
   ↓
5. Service Layer
   apps/cart/services/cart_service.py
   CartService.add_item_to_cart()
   - Check stock
   - Get/Create cart
   - Add item
   ↓
6. Selector Layer
   apps/cart/selectors/cart_selector.py
   CartSelector.get_cart_by_session()
   ↓
7. Model Layer
   apps/cart/models.py
   CartItem.save()
   ↓
8. Database
   INSERT INTO cart_items ...
   ↓
9. Signal
   apps/cart/signals.py
   (اگر نیاز باشد)
   ↓
10. Response
    Serializer.data
    ↓
11. Frontend Response
    JSON Response
```

---

## Database Schema

### Products App

**categories**
- id (PK)
- name
- parent_id (FK, nullable)
- display_order
- is_active
- created_at, updated_at

**products**
- id (PK)
- name
- description
- price (IntegerField - ریال)
- category_id (FK)
- image
- stock_quantity
- min_stock_level
- is_active
- created_at, updated_at

**stock_history**
- id (PK)
- product_id (FK)
- previous_quantity
- new_quantity
- change_type (choices)
- related_order_id (FK, nullable)
- admin_user_id (FK, nullable)
- notes
- created_at

### Cart App

**carts**
- id (PK)
- session_key
- created_at, updated_at

**cart_items**
- id (PK)
- cart_id (FK)
- product_id (FK)
- quantity
- unit_price (snapshot)
- created_at, updated_at

### Orders App

**orders**
- id (PK)
- order_number (unique)
- cart_id (FK)
- total_amount
- payment_status (choices)
- payment_transaction_id (FK, nullable)
- created_at, updated_at

**order_items**
- id (PK)
- order_id (FK)
- product_id (FK)
- product_name (snapshot)
- quantity
- unit_price
- subtotal

**invoices**
- id (PK)
- order_id (OneToOne)
- invoice_number (unique)
- pdf_file
- json_data (JSONField)
- generated_at

### Payment App

**transactions**
- id (PK)
- transaction_id (unique)
- order_id (FK)
- amount
- status (choices)
- payment_method
- gateway_name
- gateway_request_data (JSONField)
- gateway_response_data (JSONField)
- error_message
- created_at, updated_at

**payment_gateway_config**
- id (PK)
- gateway_name (choices)
- is_active
- api_key
- api_secret
- merchant_id
- terminal_id
- callback_url
- config_data (JSONField)
- created_at, updated_at

### Logs App

**system_logs**
- id (PK)
- log_type (choices)
- level (choices)
- user_id (FK, nullable)
- session_key
- action
- details (JSONField)
- ip_address
- user_agent
- created_at

**transaction_logs**
- id (PK)
- transaction_id (FK)
- log_type (choices)
- message
- request_data (JSONField, nullable)
- response_data (JSONField, nullable)
- error_details (JSONField, nullable)
- created_at

### Core App

**backups**
- id (PK)
- backup_type (choices)
- file_path
- file_size
- status (choices)
- started_at
- completed_at
- error_message

---

## API Structure

### Kiosk APIs (`/api/kiosk/`)

```
/api/kiosk/
├── products/
│   ├── GET /                    # List products
│   ├── GET /{id}/               # Product detail
│   └── GET /search/             # Search products
│
├── categories/
│   ├── GET /                    # List categories
│   └── GET /{id}/products/     # Category products
│
├── cart/
│   ├── GET /current/            # Get current cart
│   ├── GET /total/              # Get cart total
│   └── DELETE /clear/           # Clear cart
│
├── cart-items/
│   ├── GET /                    # List cart items
│   ├── POST /                   # Add item
│   ├── PUT /{id}/               # Update item
│   └── DELETE /{id}/            # Remove item
│
├── payment/
│   ├── POST /initiate/          # Initiate payment
│   ├── POST /verify/            # Verify payment
│   └── GET /status/             # Payment status
│
└── orders/
    ├── GET /{order_number}/     # Get order
    ├── GET /{order_number}/invoice/      # Download PDF
    └── GET /{order_number}/invoice/json/ # Get JSON invoice
```

### Admin APIs (`/api/admin/`)

```
/api/admin/
├── auth/
│   ├── POST /login/             # Login
│   ├── POST /logout/            # Logout
│   └── GET /me/                 # Current user
│
├── products/
│   ├── GET /                    # List products
│   ├── POST /                   # Create product
│   ├── GET /{id}/               # Product detail
│   ├── PUT /{id}/               # Update product
│   ├── DELETE /{id}/            # Delete product
│   └── PUT /{id}/update_stock/  # Update stock
│
├── categories/
│   ├── GET /                    # List categories
│   ├── POST /                   # Create category
│   ├── PUT /{id}/               # Update category
│   └── DELETE /{id}/            # Delete category
│
├── orders/
│   ├── GET /                    # List orders
│   └── GET /{id}/               # Order detail
│
├── reports/
│   ├── GET /sales/              # Sales report
│   ├── GET /sales/pdf/          # Sales report PDF
│   ├── GET /transactions/       # Transaction report
│   ├── GET /products/           # Product report
│   └── GET /stocks/              # Stock report
│
├── backups/
│   ├── GET /                    # List backups
│   ├── POST /create/            # Create backup
│   ├── GET /{id}/download/      # Download backup
│   └── DELETE /{id}/            # Delete backup
│
└── logs/
    ├── GET /system/             # System logs
    └── GET /transactions/       # Transaction logs
```

---

## Security

### Authentication
- **Kiosk APIs**: Session-based (Django Sessions)
- **Admin APIs**: Django Session Authentication

### Permissions
- **Kiosk APIs**: Public (Session-based tracking)
- **Admin APIs**: IsAuthenticated + Role-based (اختیاری)

### CORS
- تنظیم `CORS_ALLOWED_ORIGINS` در Settings
- فقط Frontend های مجاز می‌توانند درخواست بفرستند

### CSRF Protection
- فعال برای Admin APIs
- غیرفعال برای Kiosk APIs (اگر نیاز باشد)

### Data Validation
- Serializer Validation در API Layer
- Model Validation در Model Layer
- Service Layer Validation

### SQL Injection Protection
- استفاده از Django ORM (خودکار محافظت می‌شود)
- استفاده از Parameterized Queries

### XSS Protection
- Django Template Auto-escaping
- JSON Response (بدون HTML)

---

## Payment Gateway Integration

### Architecture

```
Payment Service
    ↓
Gateway Adapter (Factory Pattern)
    ↓
Base Gateway (Abstract)
    ↓
Concrete Gateway (Pasargad, Saman, etc.)
    ↓
External API
```

### Flow

```
1. PaymentService.initiate_payment()
   ↓
2. GatewayAdapter.get_gateway()
   ↓
3. Gateway.initiate_payment()
   ↓
4. External API Call
   ↓
5. Store Response
   ↓
6. Return Transaction ID
   ↓
7. Frontend redirects to Gateway
   ↓
8. User pays
   ↓
9. Gateway Webhook/Callback
   ↓
10. PaymentService.verify_payment()
    ↓
11. Update Transaction Status
    ↓
12. Create Order (if successful)
```

---

## Logging Architecture

### Log Types
1. **System Logs**: تمام عملیات سیستم
2. **Transaction Logs**: لاگ تخصصی تراکنش‌ها

### Log Levels
- INFO: عملیات عادی
- WARNING: هشدارها
- ERROR: خطاها
- CRITICAL: خطاهای بحرانی

### Logging Flow

```
Request
    ↓
Middleware (Request Logging)
    ↓
API View
    ↓
Service Layer (Action Logging)
    ↓
Log Service
    ↓
Console & File (logs/kiosk.log)
```

---

## Performance Optimization

### Database
- استفاده از `select_related` برای Foreign Keys
- استفاده از `prefetch_related` برای Many-to-Many
- Indexing روی Fields پرکاربرد
- Query Optimization در Selectors

### Caching
- Query Result Caching (اختیاری)

---

## Scalability

### Horizontal Scaling
- Stateless API (Session در Database)
- Multiple Workers (Gunicorn/uWSGI)
- Load Balancer (Nginx)

### Database Scaling
- Read Replicas (اختیاری)
- Connection Pooling

### Caching Strategy
- Cache برای Queries پرتکرار

---

## Monitoring

### Logging
- File Logging
- Error Tracking (Sentry - اختیاری)

### Health Checks
- `/health/` Endpoint
- Database Connection Check

### Metrics
- Request Count
- Response Time
- Error Rate
- Transaction Success Rate

---

**این معماری برای یک سیستم قابل مقیاس و قابل نگهداری طراحی شده است.**

