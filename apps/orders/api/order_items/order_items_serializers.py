from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.orders.models import OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, label=_('نام محصول'))
    product_price = serializers.IntegerField(source='product.price', read_only=True, label=_('قیمت محصول'))
    subtotal = serializers.IntegerField(read_only=True, label=_('جمع'))
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'product_price',
            'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']

