from rest_framework import generics
from rest_framework.response import Response
from apps.cart.api.cart.cart_serializers import CartSerializer
from apps.cart.selectors.cart_selector import CartSelector
from apps.cart.services.cart_service import CartService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.status_codes import ResponseStatusCodes


class CartCurrentAPIView(generics.GenericAPIView):
    """
    API endpoint for retrieving current cart.
    
    Returns the current cart for the session, creating one if it doesn't exist.
    """
    serializer_class = CartSerializer
    
    @custom_extend_schema(
        resource_name="CartCurrent",
        response_serializer=CartSerializer,
        status_codes=[ResponseStatusCodes.OK],
        summary="Get Current Cart",
        description="Get the current cart for the session. Creates a new cart if one doesn't exist.",
        tags=["Cart"],
        operation_id="cart_current",
    )
    def get(self, request):
        """
        Get or create cart for current session.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Cart data with items
        """
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart = CartSelector.get_cart_by_session(session_key)
        if not cart:
            cart = CartService.create_cart(session_key)
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)


class CartTotalAPIView(generics.GenericAPIView):
    """
    API endpoint for getting cart total amount.
    
    Returns the total amount of all items in the cart.
    """
    @custom_extend_schema(
        resource_name="CartTotal",
        status_codes=[ResponseStatusCodes.OK],
        summary="Get Cart Total",
        description="Get the total amount of all items in the current cart.",
        tags=["Cart"],
        operation_id="cart_total",
    )
    def get(self, request):
        """
        Calculate and return cart total.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Dictionary with total amount in Rial
        """
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart = CartSelector.get_cart_by_session(session_key)
        if not cart:
            return Response({'total': 0})
        
        total = CartSelector.calculate_cart_total(cart.id)
        return Response({'total': total})


class CartClearAPIView(generics.GenericAPIView):
    """
    API endpoint for clearing cart.
    
    Removes all items from the current cart.
    """
    @custom_extend_schema(
        resource_name="CartClear",
        status_codes=[ResponseStatusCodes.NO_CONTENT],
        summary="Clear Cart",
        description="Remove all items from the current cart.",
        tags=["Cart"],
        operation_id="cart_clear",
    )
    def delete(self, request):
        """
        Clear all items from cart.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: 204 No Content on success
        """
        session_key = request.session.session_key
        if not session_key:
            return Response({'message': 'Cart is already empty'}, status=204)
        
        cart = CartSelector.get_cart_by_session(session_key)
        if cart:
            CartService.clear_cart(cart.id)
        
        return Response(status=204)

