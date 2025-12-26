from rest_framework import generics, status
from rest_framework.response import Response
from apps.orders.models import Order
from apps.orders.api.orders.orders_serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderCreateSerializer
)
from apps.orders.selectors.order_selector import OrderSelector
from apps.orders.services.order_service import OrderService


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    
    def get_queryset(self):
        session_key = self.request.session.session_key
        if not session_key:
            return Order.objects.none()
        
        return OrderSelector.get_orders_by_session(session_key)


class OrderCreateAPIView(generics.GenericAPIView):
    serializer_class = OrderCreateSerializer
    
    def post(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        order = OrderService.create_order_from_cart(session_key)
        
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        session_key = self.request.session.session_key
        if not session_key:
            return Order.objects.none()
        
        return OrderSelector.get_orders_by_session(session_key)

