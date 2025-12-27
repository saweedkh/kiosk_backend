from typing import Optional
from django.db import transaction
from apps.cart.models import Cart, CartItem
from apps.cart.selectors.cart_selector import CartSelector
from apps.products.services.product_service import ProductService
from apps.logs.services.log_service import LogService
from apps.core.exceptions.order import InsufficientStockException


class CartService:
    """
    Shopping cart management service.
    
    This class contains all business logic related to shopping cart operations.
    """
    
    @staticmethod
    def create_cart(session_key: str) -> Cart:
        """
        Create or get existing cart for a session.
        
        Args:
            session_key: Django session key
            
        Returns:
            Cart: Cart instance (created or existing)
        """
        cart, created = Cart.objects.get_or_create_by_session(session_key)
        if created:
            LogService.log_info(
                'order',
                'cart_created',
                details={'cart_id': cart.id, 'session_key': session_key}
            )
        return cart
    
    @staticmethod
    @transaction.atomic
    def add_item_to_cart(session_key: str, product_id: int, quantity: int = 1) -> CartItem:
        """
        Add product to cart or update quantity if item already exists.
        
        Args:
            session_key: Django session key
            product_id: Product ID to add
            quantity: Quantity to add (default: 1)
            
        Returns:
            CartItem: Cart item instance (created or updated)
            
        Raises:
            InsufficientStockException: If insufficient stock available
            Product.DoesNotExist: If product does not exist
        """
        cart = CartService.create_cart(session_key)
        
        ProductService.check_stock(product_id, quantity)
        
        product = ProductService.get_product_details(product_id)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'unit_price': product.price
            }
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        LogService.log_info(
            'order',
            'item_added_to_cart',
            details={
                'cart_id': cart.id,
                'product_id': product_id,
                'quantity': cart_item.quantity,
                'session_key': session_key
            }
        )
        
        return cart_item
    
    @staticmethod
    @transaction.atomic
    def update_cart_item(cart_item_id: int, quantity: int) -> Optional[CartItem]:
        """
        Update cart item quantity or remove if quantity is zero or negative.
        
        Args:
            cart_item_id: Cart item ID to update
            quantity: New quantity (if <= 0, item will be removed)
            
        Returns:
            CartItem: Updated cart item instance, or None if removed
            
        Raises:
            CartItem.DoesNotExist: If cart item does not exist
            InsufficientStockException: If insufficient stock available
        """
        cart_item = CartItem.objects.select_related('product').get(id=cart_item_id)
        
        if quantity <= 0:
            cart_item.delete()
            LogService.log_info(
                'order',
                'item_removed_from_cart',
                details={'cart_item_id': cart_item_id}
            )
            return None
        
        ProductService.check_stock(cart_item.product_id, quantity)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        LogService.log_info(
            'order',
            'cart_item_updated',
            details={
                'cart_item_id': cart_item_id,
                'quantity': quantity
            }
        )
        
        return cart_item
    
    @staticmethod
    @transaction.atomic
    def remove_item_from_cart(cart_item_id: int) -> None:
        """
        Remove item from cart.
        
        Args:
            cart_item_id: Cart item ID to remove
            
        Raises:
            CartItem.DoesNotExist: If cart item does not exist
        """
        cart_item = CartItem.objects.get(id=cart_item_id)
        cart_item.delete()
        
        LogService.log_info(
            'order',
            'item_removed_from_cart',
            details={'cart_item_id': cart_item_id}
        )
    
    @staticmethod
    @transaction.atomic
    def clear_cart(cart_id: int) -> None:
        """
        Clear all items from cart.
        
        Args:
            cart_id: Cart ID to clear
        """
        CartItem.objects.filter(cart_id=cart_id).delete()
        
        LogService.log_info(
            'order',
            'cart_cleared',
            details={'cart_id': cart_id}
        )

