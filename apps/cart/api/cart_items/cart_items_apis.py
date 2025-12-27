from rest_framework import generics, status
from rest_framework.response import Response
from apps.cart.models import CartItem
from apps.cart.api.cart_items.cart_items_serializers import (
    CartItemSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer
)
from apps.cart.selectors.cart_selector import CartSelector
from apps.cart.services.cart_service import CartService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.parameter_serializers import CartItemPathSerializer
from apps.core.api.status_codes import ResponseStatusCodes


class CartItemListAPIView(generics.ListAPIView):
    """
    API endpoint for listing cart items.
    
    Returns all items in the current session's cart.
    """
    serializer_class = CartItemSerializer
    
    @custom_extend_schema(
        resource_name="CartItemList",
        response_serializer=CartItemSerializer,
        status_codes=[ResponseStatusCodes.OK_ALL],
        summary="List Cart Items",
        description="Get all items in the current session's shopping cart.",
        tags=["Cart"],
        operation_id="cart_items_list",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get queryset of cart items for current session.
        
        Returns:
            QuerySet: QuerySet of cart items
        """
        session_key = self.request.session.session_key
        if not session_key:
            return CartItem.objects.none()
        
        cart = CartSelector.get_cart_by_session(session_key)
        if cart:
            return CartSelector.get_cart_items_with_products(cart.id)
        return CartItem.objects.none()


class CartItemCreateAPIView(generics.GenericAPIView):
    """
    API endpoint for adding item to cart.
    
    Adds a product to the cart or increases quantity if already exists.
    """
    serializer_class = CartItemCreateSerializer
    
    @custom_extend_schema(
        resource_name="CartItemCreate",
        parameters=[CartItemCreateSerializer],
        request_serializer=CartItemCreateSerializer,
        response_serializer=CartItemSerializer,
        status_codes=[
            ResponseStatusCodes.CREATED,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
        ],
        summary="Add Item to Cart",
        description="Add a product to the shopping cart. If the product already exists in the cart, the quantity will be increased.",
        tags=["Cart"],
        operation_id="cart_items_create",
    )
    def post(self, request):
        """
        Add item to cart.
        
        Args:
            request: HTTP request object with product_id and quantity
            
        Returns:
            Response: Created cart item data
            
        Raises:
            ValidationError: If product_id is invalid or insufficient stock
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart_item = CartService.add_item_to_cart(
            session_key=session_key,
            product_id=serializer.validated_data['product_id'],
            quantity=serializer.validated_data.get('quantity', 1)
        )
        
        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED
        )


class CartItemUpdateAPIView(generics.GenericAPIView):
    """
    API endpoint for updating cart item quantity.
    
    Updates the quantity of a cart item. If quantity is 0 or negative,
    the item is removed from cart.
    """
    serializer_class = CartItemUpdateSerializer
    
    @custom_extend_schema(
        resource_name="CartItemUpdate",
        parameters=[CartItemPathSerializer, CartItemUpdateSerializer],
        request_serializer=CartItemUpdateSerializer,
        response_serializer=CartItemSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.NO_CONTENT,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
        ],
        summary="Update Cart Item",
        description="Update the quantity of a cart item. If quantity is set to 0 or negative, the item will be removed from the cart.",
        tags=["Cart"],
        operation_id="cart_items_update",
    )
    def put(self, request, pk):
        """
        Update cart item quantity.
        
        Args:
            request: HTTP request object with quantity
            pk: Cart item ID
            
        Returns:
            Response: Updated cart item data or 204 if removed
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_item = CartService.update_cart_item(
            cart_item_id=pk,
            quantity=serializer.validated_data['quantity']
        )
        
        if updated_item is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(CartItemSerializer(updated_item).data)


class CartItemDeleteAPIView(generics.GenericAPIView):
    """
    API endpoint for removing item from cart.
    
    Removes a specific item from the cart.
    """
    @custom_extend_schema(
        resource_name="CartItemDelete",
        parameters=[CartItemPathSerializer],
        status_codes=[
            ResponseStatusCodes.NO_CONTENT,
            ResponseStatusCodes.NOT_FOUND,
        ],
        summary="Remove Cart Item",
        description="Remove a specific item from the shopping cart.",
        tags=["Cart"],
        operation_id="cart_items_delete",
    )
    def delete(self, request, pk):
        """
        Remove item from cart.
        
        Args:
            request: HTTP request object
            pk: Cart item ID
            
        Returns:
            Response: 204 No Content on success
        """
        CartService.remove_item_from_cart(cart_item_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

