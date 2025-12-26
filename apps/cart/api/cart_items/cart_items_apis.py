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


class CartItemListAPIView(generics.ListAPIView):
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        session_key = self.request.session.session_key
        if not session_key:
            return CartItem.objects.none()
        
        cart = CartSelector.get_cart_by_session(session_key)
        if cart:
            return CartSelector.get_cart_items_with_products(cart.id)
        return CartItem.objects.none()


class CartItemCreateAPIView(generics.GenericAPIView):
    serializer_class = CartItemCreateSerializer
    
    def post(self, request):
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
    serializer_class = CartItemUpdateSerializer
    
    def put(self, request, pk):
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
    def delete(self, request, pk):
        CartService.remove_item_from_cart(cart_item_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

