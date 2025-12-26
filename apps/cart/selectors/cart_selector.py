from django.db.models import Sum, F, Prefetch
from apps.cart.models import Cart, CartItem


class CartSelector:
    @staticmethod
    def get_cart_by_session(session_key):
        return Cart.objects.prefetch_related(
            Prefetch(
                'items',
                queryset=CartItem.objects.select_related('product', 'product__category')
            )
        ).filter(session_key=session_key).first()
    
    @staticmethod
    def get_cart_items_with_products(cart_id):
        return CartItem.objects.filter(
            cart_id=cart_id
        ).select_related('product', 'product__category')
    
    @staticmethod
    def calculate_cart_total(cart_id):
        result = CartItem.objects.filter(
            cart_id=cart_id
        ).aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )
        return result['total'] or 0
    
    @staticmethod
    def get_cart_item_by_product(cart_id, product_id):
        return CartItem.objects.select_related(
            'product'
        ).filter(
            cart_id=cart_id,
            product_id=product_id
        ).first()

