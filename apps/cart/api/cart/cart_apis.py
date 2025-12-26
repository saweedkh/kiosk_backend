from rest_framework import generics
from rest_framework.response import Response
from apps.cart.api.cart.cart_serializers import CartSerializer
from apps.cart.selectors.cart_selector import CartSelector
from apps.cart.services.cart_service import CartService


class CartCurrentAPIView(generics.GenericAPIView):
    serializer_class = CartSerializer
    
    def get(self, request):
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
    def get(self, request):
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
    def delete(self, request):
        session_key = request.session.session_key
        if not session_key:
            return Response({'message': 'Cart is already empty'}, status=204)
        
        cart = CartSelector.get_cart_by_session(session_key)
        if cart:
            CartService.clear_cart(cart.id)
        
        return Response(status=204)

