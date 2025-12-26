from django.core.exceptions import ValidationError
from apps.products.models import Product
from apps.products.selectors.product_selector import ProductSelector
from apps.logs.services.log_service import LogService
from apps.core.exceptions.order import InsufficientStockException


class ProductService:
    @staticmethod
    def create_product(validated_data):
        product = Product.objects.create(**validated_data)
        
        LogService.log_info(
            'product',
            'product_created',
            details={'product_id': product.id, 'name': product.name}
        )
        
        return product
    
    @staticmethod
    def update_product(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        LogService.log_info(
            'product',
            'product_updated',
            details={'product_id': instance.id, 'name': instance.name}
        )
        
        return instance
    
    @staticmethod
    def get_active_products():
        return ProductSelector.get_active_products()
    
    @staticmethod
    def get_product_details(product_id):
        try:
            return ProductSelector.get_product_with_details(product_id)
        except Product.DoesNotExist:
            LogService.log_error(
                'product',
                'product_not_found',
                details={'product_id': product_id}
            )
            raise
    
    @staticmethod
    def search_products(query):
        return ProductSelector.search_products(query)
    
    @staticmethod
    def check_stock(product_id, quantity):
        product = Product.objects.get(id=product_id)
        if product.stock_quantity < quantity:
            LogService.log_warning(
                'product',
                'insufficient_stock',
                details={
                    'product_id': product_id,
                    'requested': quantity,
                    'available': product.stock_quantity
                }
            )
            raise InsufficientStockException(
                f'Insufficient stock. Available: {product.stock_quantity}, Requested: {quantity}'
            )
        return product

