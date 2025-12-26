from django.contrib.auth import get_user_model
from apps.products.models import Product, StockHistory
from apps.logs.services.log_service import LogService

User = get_user_model()


class StockService:
    @staticmethod
    def update_stock(product_id, new_quantity, change_type='manual', admin_user=None, notes='', related_order_id=None):
        product = Product.objects.get(id=product_id)
        previous_quantity = product.stock_quantity
        
        product.stock_quantity = new_quantity
        product.save()
        
        StockHistory.objects.create(
            product=product,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            change_type=change_type,
            admin_user=admin_user,
            notes=notes,
            related_order_id=related_order_id
        )
        
        LogService.log_info(
            'product',
            'stock_updated',
            user=admin_user,
            details={
                'product_id': product_id,
                'previous_quantity': previous_quantity,
                'new_quantity': new_quantity,
                'change_type': change_type
            }
        )
        
        return product
    
    @staticmethod
    def decrease_stock(product_id, quantity, related_order_id=None):
        product = Product.objects.get(id=product_id)
        new_quantity = product.stock_quantity - quantity
        
        if new_quantity < 0:
            LogService.log_error(
                'product',
                'stock_decrease_failed',
                details={
                    'product_id': product_id,
                    'current_stock': product.stock_quantity,
                    'requested_decrease': quantity
                }
            )
            raise ValueError('Insufficient stock')
        
        return StockService.update_stock(
            product_id=product_id,
            new_quantity=new_quantity,
            change_type='sale',
            notes=f'Decreased by {quantity}',
            related_order_id=related_order_id
        )
    
    @staticmethod
    def increase_stock(product_id, quantity, admin_user=None, notes=''):
        product = Product.objects.get(id=product_id)
        new_quantity = product.stock_quantity + quantity
        
        return StockService.update_stock(
            product_id=product_id,
            new_quantity=new_quantity,
            change_type='increase',
            admin_user=admin_user,
            notes=notes or f'Increased by {quantity}'
        )

