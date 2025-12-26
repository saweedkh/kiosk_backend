from django.db import transaction
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.orders.selectors.order_selector import OrderSelector
from apps.cart.selectors.cart_selector import CartSelector
from apps.products.services.stock_service import StockService
from apps.logs.services.log_service import LogService
from apps.core.exceptions.order import OrderNotFoundException


class OrderService:
    @staticmethod
    def generate_order_number():
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(timezone.now().microsecond)[:4]
        return f"ORD-{timestamp}-{random_suffix}"
    
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(session_key):
        cart = CartSelector.get_cart_by_session(session_key)
        if not cart or not cart.items.exists():
            raise ValueError('Cart is empty')
        
        order_number = OrderService.generate_order_number()
        cart_items = CartSelector.get_cart_items_with_products(cart.id)
        total_amount = CartSelector.calculate_cart_total(cart.id)
        
        order = Order.objects.create(
            order_number=order_number,
            session_key=session_key,
            status='pending',
            total_amount=total_amount,
            payment_status='pending'
        )
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )
            
            StockService.decrease_stock(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                related_order_id=order.id
            )
        
        LogService.log_info(
            'order',
            'order_created',
            details={
                'order_id': order.id,
                'order_number': order_number,
                'session_key': session_key,
                'total_amount': total_amount
            }
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def update_order_status(order_id, status):
        order = OrderSelector.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundException()
        
        old_status = order.status
        order.status = status
        order.save()
        
        LogService.log_info(
            'order',
            'order_status_updated',
            details={
                'order_id': order.id,
                'order_number': order.order_number,
                'old_status': old_status,
                'new_status': status
            }
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def update_payment_status(order_id, payment_status):
        order = OrderSelector.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundException()
        
        old_status = order.payment_status
        order.payment_status = payment_status
        
        if payment_status == 'paid':
            order.status = 'paid'
        
        order.save()
        
        LogService.log_info(
            'order',
            'payment_status_updated',
            details={
                'order_id': order.id,
                'order_number': order.order_number,
                'old_status': old_status,
                'new_status': payment_status
            }
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order_id):
        order = OrderSelector.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundException()
        
        if order.status in ['completed', 'cancelled']:
            raise ValueError(f'Cannot cancel order with status: {order.status}')
        
        for order_item in order.items.all():
            StockService.increase_stock(
                product_id=order_item.product_id,
                quantity=order_item.quantity,
                notes=f'Order {order.order_number} cancelled'
            )
        
        order.status = 'cancelled'
        order.save()
        
        LogService.log_info(
            'order',
            'order_cancelled',
            details={
                'order_id': order.id,
                'order_number': order.order_number
            }
        )
        
        return order

