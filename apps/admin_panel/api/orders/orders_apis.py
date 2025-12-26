from rest_framework import generics, status
from rest_framework.response import Response
from apps.orders.models import Order
from apps.admin_panel.api.orders.orders_serializers import (
    AdminOrderSerializer,
    AdminOrderListSerializer,
    UpdateOrderStatusSerializer
)
from apps.admin_panel.api.orders.orders_filters import AdminOrderFilter
from apps.admin_panel.api.permissions import IsAdminUser
from apps.orders.services.order_service import OrderService


class AdminOrderListAPIView(generics.ListAPIView):
    queryset = Order.objects.prefetch_related('items__product').all()
    serializer_class = AdminOrderListSerializer
    permission_classes = [IsAdminUser]
    filterset_class = AdminOrderFilter


class AdminOrderRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Order.objects.prefetch_related('items__product').all()
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]


class AdminOrderUpdateStatusAPIView(generics.GenericAPIView):
    queryset = Order.objects.all()
    serializer_class = UpdateOrderStatusSerializer
    permission_classes = [IsAdminUser]
    
    def put(self, request, pk):
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        OrderService.update_order_status(order.id, serializer.validated_data['status'])
        
        order.refresh_from_db()
        return Response(AdminOrderSerializer(order).data)

