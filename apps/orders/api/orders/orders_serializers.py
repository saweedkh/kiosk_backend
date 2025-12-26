from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, label=_('نام محصول'))
    product_price = serializers.IntegerField(source='product.price', read_only=True, label=_('قیمت محصول'))
    subtotal = serializers.IntegerField(read_only=True, label=_('جمع'))
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_price',
            'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'session_key', 'status',
            'payment_status', 'total_amount', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'session_key', 'status',
            'payment_status', 'total_amount', 'created_at', 'updated_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status',
            'total_amount', 'created_at'
        ]
        read_only_fields = ['id', 'order_number', 'status', 'payment_status', 'total_amount', 'created_at']


class OrderCreateSerializer(serializers.Serializer):
    pass

