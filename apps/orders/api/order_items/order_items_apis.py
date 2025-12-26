from rest_framework import generics
from apps.orders.models import OrderItem
from apps.orders.api.order_items.order_items_serializers import OrderItemSerializer
from apps.orders.selectors.order_selector import OrderSelector


class OrderItemListAPIView(generics.ListAPIView):
    serializer_class = OrderItemSerializer
    
    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        if not order_id:
            return OrderItem.objects.none()
        
        return OrderSelector.get_order_items(order_id)

