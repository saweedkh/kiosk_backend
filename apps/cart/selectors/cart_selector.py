from typing import Optional
from django.db.models import Sum, F, Prefetch, QuerySet
from apps.cart.models import Cart, CartItem


class CartSelector:
    """
    Cart query selector.
    
    This class encapsulates all database queries related to carts
    with optimized queries using select_related and prefetch_related.
    """
    
    @staticmethod
    def get_cart_by_session(session_key: str) -> Optional[Cart]:
        """
        Get cart by session key with all items and product details prefetched.
        
        Args:
            session_key: Django session key
            
        Returns:
            Optional[Cart]: Cart instance if found, None otherwise
        """
        return Cart.objects.prefetch_related(
            Prefetch(
                'items',
                queryset=CartItem.objects.select_related('product', 'product__category')
            )
        ).filter(session_key=session_key).first()
    
    @staticmethod
    def get_cart_items_with_products(cart_id: int) -> QuerySet[CartItem]:
        """
        Get all cart items for a cart with product and category information.
        
        Args:
            cart_id: Cart ID
            
        Returns:
            QuerySet[CartItem]: QuerySet of cart items with product and category prefetched
        """
        return CartItem.objects.filter(
            cart_id=cart_id
        ).select_related('product', 'product__category')
    
    @staticmethod
    def calculate_cart_total(cart_id: int) -> int:
        """
        Calculate total amount of cart items.
        
        Args:
            cart_id: Cart ID
            
        Returns:
            int: Total cart amount in Rial (0 if cart is empty)
        """
        result = CartItem.objects.filter(
            cart_id=cart_id
        ).aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )
        return result['total'] or 0
    
    @staticmethod
    def get_cart_item_by_product(cart_id: int, product_id: int) -> Optional[CartItem]:
        """
        Get cart item by cart and product IDs.
        
        Args:
            cart_id: Cart ID
            product_id: Product ID
            
        Returns:
            Optional[CartItem]: Cart item if found, None otherwise
        """
        return CartItem.objects.select_related(
            'product'
        ).filter(
            cart_id=cart_id,
            product_id=product_id
        ).first()

