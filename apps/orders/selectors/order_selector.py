from django.db.models import Sum, F, Prefetch
from apps.orders.models import Order, OrderItem


class OrderSelector:
    @staticmethod
    def get_order_by_number(order_number):
        return Order.objects.prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('product', 'product__category')
            )
        ).filter(order_number=order_number).first()
    
    @staticmethod
    def get_order_by_id(order_id):
        return Order.objects.prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('product', 'product__category')
            )
        ).filter(id=order_id).first()
    
    @staticmethod
    def get_orders_by_session(session_key):
        return Order.objects.prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('product')
            )
        ).filter(session_key=session_key).order_by('-created_at')
    
    @staticmethod
    def get_order_items(order_id):
        return OrderItem.objects.filter(
            order_id=order_id
        ).select_related('product', 'product__category')
    
    @staticmethod
    def calculate_order_total(order_id):
        result = OrderItem.objects.filter(
            order_id=order_id
        ).aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )
        return result['total'] or 0
    
    @staticmethod
    def get_pending_orders():
        return Order.objects.filter(status='pending').order_by('-created_at')
    
    @staticmethod
    def get_completed_orders():
        return Order.objects.filter(status='completed').order_by('-created_at')
    
    @staticmethod
    def get_orders_by_status(status):
        return Order.objects.filter(status=status).order_by('-created_at')

