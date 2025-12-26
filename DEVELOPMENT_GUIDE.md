# راهنمای توسعه پروژه کیوسک

## 📋 فهرست مطالب
1. [قوانین کدنویسی](#قوانین-کدنویسی)
2. [Best Practices](#best-practices)
3. [Git Workflow](#git-workflow)
4. [Testing Guidelines](#testing-guidelines)
5. [Code Review Checklist](#code-review-checklist)
6. [Debugging Tips](#debugging-tips)

---

## قوانین کدنویسی

### Python Style Guide
- از PEP 8 پیروی کنید
- استفاده از Black برای Formatting (اختیاری)
- استفاده از Flake8 برای Linting

### Naming Conventions

#### Models
```python
# Singular, PascalCase
class Product(models.Model):
    pass

class OrderItem(models.Model):
    pass
```

#### Views/ViewSets
```python
# PascalCase با ViewSet suffix
class ProductViewSet(viewsets.ModelViewSet):
    pass

class SalesReportView(views.APIView):
    pass
```

#### Serializers
```python
# PascalCase با Serializer suffix
class ProductSerializer(serializers.ModelSerializer):
    pass

class ProductCreateSerializer(serializers.ModelSerializer):
    pass
```

#### Services
```python
# PascalCase با Service suffix
class ProductService:
    pass

class CartService:
    pass
```

#### Selectors
```python
# PascalCase با Selector suffix
class ProductSelector:
    pass

class CartSelector:
    pass
```

#### Functions/Methods
```python
# snake_case
def get_active_products():
    pass

def calculate_cart_total():
    pass
```

#### Variables
```python
# snake_case
product_list = []
cart_total = 0
```

### File Naming
- فایل‌های Python: `snake_case.py`
- فایل‌های API: نام API (مثلاً `products.py`)
- فایل‌های Test: `test_*.py`

---

## Best Practices

### 1. Service Layer Pattern

**✅ خوب:**
```python
# Service Layer
class ProductService:
    @staticmethod
    def create_product(validated_data):
        # Validation
        if validated_data['price'] < 0:
            raise ValidationError("Price cannot be negative")
        
        # Business Logic
        product = Product.objects.create(**validated_data)
        
        # Logging
        LogService.create_system_log(
            log_type='product',
            action='product_created',
            details={'product_id': product.id}
        )
        
        return product
```

**❌ بد:**
```python
# Business Logic در View
class ProductViewSet(viewsets.ModelViewSet):
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Business Logic در View - بد!
        if serializer.validated_data['price'] < 0:
            return Response({'error': 'Invalid price'}, status=400)
        
        product = Product.objects.create(**serializer.validated_data)
        return Response(serializer.data)
```

### 2. Selector Pattern

**✅ خوب:**
```python
# Selector Layer
class ProductSelector:
    @staticmethod
    def get_active_products():
        return Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0
        ).select_related('category')
```

**❌ بد:**
```python
# Query در View - بد!
class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Product.objects.filter(is_active=True)
        # بدون select_related - N+1 Problem!
```

### 3. Error Handling

**✅ خوب:**
```python
from apps.core.exceptions import ProductNotFoundException

class ProductService:
    @staticmethod
    def get_product(product_id):
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ProductNotFoundException(f"Product {product_id} not found")
```

**❌ بد:**
```python
# Generic Exception - بد!
class ProductService:
    @staticmethod
    def get_product(product_id):
        try:
            return Product.objects.get(id=product_id)
        except Exception as e:
            raise Exception(str(e))  # خیلی Generic!
```

### 4. Type Hints

**✅ خوب:**
```python
from typing import List, Optional
from apps.products.models import Product

class ProductService:
    @staticmethod
    def get_active_products() -> List[Product]:
        return list(Product.objects.active())
    
    @staticmethod
    def get_product(product_id: int) -> Optional[Product]:
        return Product.objects.filter(id=product_id).first()
```

### 5. Docstrings

**✅ خوب:**
```python
class ProductService:
    @staticmethod
    def create_product(validated_data: dict) -> Product:
        """
        ایجاد محصول جدید
        
        Args:
            validated_data: داده‌های معتبر محصول
            
        Returns:
            Product: محصول ایجاد شده
            
        Raises:
            ValidationError: در صورت داده نامعتبر
        """
        product = Product.objects.create(**validated_data)
        return product
```

### 6. Constants

**✅ خوب:**
```python
# apps/products/constants.py
class ProductStatus:
    ACTIVE = 'active'
    INACTIVE = 'inactive'

class StockChangeType:
    INCREASE = 'increase'
    DECREASE = 'decrease'
    SALE = 'sale'
    MANUAL = 'manual'
```

**❌ بد:**
```python
# Magic Strings - بد!
if product.status == 'active':  # چه می‌شود اگر typo کنیم؟
    pass
```

---

## Git Workflow

### Branch Naming
```
feature/product-management
bugfix/cart-total-calculation
hotfix/payment-error
refactor/service-layer
```

### Commit Messages
```
feat: add product search functionality
fix: fix cart total calculation
refactor: move business logic to service layer
docs: update API documentation
test: add tests for product service
```

### Workflow
1. Create Branch: `git checkout -b feature/product-management`
2. Make Changes
3. Commit: `git commit -m "feat: add product search"`
4. Push: `git push origin feature/product-management`
5. Create Pull Request
6. Code Review
7. Merge

---

## Testing Guidelines

### Unit Tests

**Structure:**
```python
# apps/products/tests/test_services.py
from django.test import TestCase
from apps.products.services.product_service import ProductService
from apps.products.models import Product

class ProductServiceTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
    
    def test_create_product(self):
        data = {
            'name': 'Test Product',
            'price': 100000,
            'category': self.category
        }
        product = ProductService.create_product(data)
        self.assertIsNotNone(product.id)
        self.assertEqual(product.name, 'Test Product')
    
    def test_create_product_negative_price(self):
        data = {
            'name': 'Test Product',
            'price': -1000,
            'category': self.category
        }
        with self.assertRaises(ValidationError):
            ProductService.create_product(data)
```

### API Tests

**Structure:**
```python
# apps/products/tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status

class ProductAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            price=100000,
            category=self.category
        )
    
    def test_list_products(self):
        url = '/api/kiosk/products/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_product_detail(self):
        url = f'/api/kiosk/products/{self.product.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')
```

### Test Coverage
- حداقل 80% Coverage
- تمام Services باید Test داشته باشند
- تمام API Endpoints باید Test داشته باشند
- Critical Paths باید Integration Test داشته باشند

---

## Code Review Checklist

### قبل از Submit PR

- [ ] تمام Tests پاس می‌شوند
- [ ] Code Style رعایت شده (PEP 8)
- [ ] Type Hints اضافه شده
- [ ] Docstrings نوشته شده
- [ ] No Magic Numbers/Strings
- [ ] Error Handling مناسب
- [ ] Logging اضافه شده (در صورت نیاز)
- [ ] Migration Files ایجاد شده (اگر Model تغییر کرده)
- [ ] API Documentation به‌روز شده
- [ ] README به‌روز شده (اگر نیاز باشد)

### Code Review Points

1. **Architecture**
   - آیا Business Logic در Service Layer است؟
   - آیا Queries در Selector Layer هستند؟
   - آیا Code Reusable است؟

2. **Performance**
   - آیا N+1 Query Problem وجود دارد؟
   - آیا از select_related/prefetch_related استفاده شده؟
   - آیا Query Optimization انجام شده؟

3. **Security**
   - آیا Input Validation انجام شده؟
   - آیا Permissions درست تنظیم شده؟
   - آیا SQL Injection محافظت شده؟

4. **Error Handling**
   - آیا Exceptions مناسب استفاده شده؟
   - آیا Error Messages واضح هستند؟
   - آیا Error Logging انجام شده؟

5. **Testing**
   - آیا Tests کافی نوشته شده؟
   - آیا Edge Cases پوشش داده شده؟
   - آیا Tests Maintainable هستند؟

---

## Debugging Tips

### 1. Django Debug Toolbar
```python
# config/settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### 2. Logging
```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Function called")
    logger.debug("Debug information")
    logger.error("Error occurred", exc_info=True)
```

### 3. Django Shell
```bash
python manage.py shell
```

```python
from apps.products.models import Product
from apps.products.services.product_service import ProductService

# Test در Shell
products = ProductService.get_active_products()
```

### 4. Database Queries Debugging
```python
from django.db import connection

# در View یا Service
def my_view(request):
    # Your code
    print(len(connection.queries))  # تعداد Queries
    for query in connection.queries:
        print(query['sql'])
```

### 5. API Testing با curl
```bash
# Test API
curl -X GET http://localhost:8000/api/kiosk/products/

# با Authentication
curl -X GET http://localhost:8000/api/admin/products/ \
  -H "Cookie: sessionid=your_session_id"
```

### 6. Postman Collection
- ایجاد Postman Collection برای تمام APIs
- استفاده برای Testing و Debugging

---

## Common Issues & Solutions

### 1. N+1 Query Problem

**Problem:**
```python
# بد - N+1 Query
products = Product.objects.all()
for product in products:
    print(product.category.name)  # یک Query برای هر product!
```

**Solution:**
```python
# خوب - با select_related
products = Product.objects.select_related('category').all()
for product in products:
    print(product.category.name)  # فقط یک Query!
```

### 2. Circular Import

**Problem:**
```python
# apps/products/services/product_service.py
from apps.orders.services.order_service import OrderService

# apps/orders/services/order_service.py
from apps.products.services.product_service import ProductService
```

**Solution:**
- استفاده از Lazy Import
- یا Refactor کردن Code

### 3. Migration Conflicts

**Solution:**
```bash
# Reset Migrations (فقط در Development!)
python manage.py migrate --fake-initial
```

### 4. Session Issues

**Solution:**
```python
# در View
if not request.session.session_key:
    request.session.create()
```

---

## Performance Tips

### 1. Query Optimization
- استفاده از `select_related` برای Foreign Keys
- استفاده از `prefetch_related` برای Many-to-Many
- استفاده از `only()` و `defer()` برای Fields خاص

### 2. Caching
```python
from django.core.cache import cache

def get_products():
    cache_key = 'active_products'
    products = cache.get(cache_key)
    if products is None:
        products = list(Product.objects.active())
        cache.set(cache_key, products, 300)  # 5 minutes
    return products
```

### 3. Pagination
- همیشه از Pagination استفاده کنید
- Page Size مناسب انتخاب کنید (20-50)

### 4. Background Tasks
- Tasks سنگین را در Celery اجرا کنید
- مثال: Backup، Email Sending، Report Generation

---

## Documentation

### Code Documentation
- Docstrings برای تمام Functions/Classes
- Type Hints برای تمام Functions
- Comments برای Logic پیچیده

### API Documentation
- استفاده از drf-spectacular یا drf-yasg
- اضافه کردن Examples به Serializers
- مستندسازی تمام Endpoints

---

## نکات مهم

1. **همیشه Tests بنویسید** قبل از Submit Code
2. **Code Review انجام دهید** قبل از Merge
3. **Documentation به‌روز کنید** وقتی Feature جدید اضافه می‌کنید
4. **Performance را در نظر بگیرید** برای Queries
5. **Security را جدی بگیرید** برای تمام Inputs

---

**موفق باشید در توسعه! 🚀**

