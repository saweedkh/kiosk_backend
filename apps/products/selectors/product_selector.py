from django.db.models import Q, F, Prefetch
from apps.products.models import Product


class ProductSelector:
    @staticmethod
    def get_active_products():
        return Product.objects.active().select_related('category')
    
    @staticmethod
    def get_products_with_stock():
        return Product.objects.filter(
            stock_quantity__gt=0,
            is_active=True
        ).select_related('category')
    
    @staticmethod
    def get_products_by_category(category_id):
        return Product.objects.filter(
            category_id=category_id,
            is_active=True,
            stock_quantity__gt=0
        ).select_related('category')
    
    @staticmethod
    def get_low_stock_products():
        return Product.objects.low_stock().select_related('category')
    
    @staticmethod
    def search_products(query):
        return Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query),
            is_active=True
        ).select_related('category')
    
    @staticmethod
    def get_product_with_details(product_id):
        return Product.objects.select_related(
            'category'
        ).prefetch_related(
            'stock_history'
        ).get(id=product_id)
    
    @staticmethod
    def get_all_products():
        return Product.objects.all().select_related('category')

