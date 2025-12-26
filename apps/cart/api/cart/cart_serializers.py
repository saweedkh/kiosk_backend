from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.cart.models import Cart, CartItem


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


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField(label=_('مجموع'))
    
    class Meta:
        model = Cart
        fields = ['id', 'session_key', 'items', 'total', 'created_at', 'updated_at']
        read_only_fields = ['id', 'session_key', 'total', 'created_at', 'updated_at']
    
    def get_total(self, obj):
        from apps.cart.selectors.cart_selector import CartSelector
        return CartSelector.calculate_cart_total(obj.id)

