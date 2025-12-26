from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.cart.models import CartItem


class CartItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(label=_('شناسه محصول'))
    quantity = serializers.IntegerField(default=1, min_value=1, label=_('تعداد'))


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, label=_('تعداد'))


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, label=_('نام محصول'))
    product_price = serializers.IntegerField(source='product.price', read_only=True, label=_('قیمت محصول'))
    subtotal = serializers.IntegerField(read_only=True, label=_('جمع'))
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_price',
            'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']

