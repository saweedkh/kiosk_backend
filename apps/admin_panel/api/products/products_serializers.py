from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.products.models import Product


class AdminProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, label=_('نام دسته‌بندی'))
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category', 'category_name',
            'image', 'stock_quantity', 'min_stock_level', 'is_active',
            'is_in_stock', 'is_low_stock', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_in_stock', 'is_low_stock', 'created_at', 'updated_at']


class AdminProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, label=_('نام دسته‌بندی'))
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'category_name', 'stock_quantity',
            'is_active', 'is_in_stock', 'is_low_stock'
        ]
        read_only_fields = ['id', 'is_in_stock', 'is_low_stock']


class UpdateStockSerializer(serializers.Serializer):
    stock_quantity = serializers.IntegerField(min_value=0, label=_('موجودی'))
    notes = serializers.CharField(required=False, allow_blank=True, label=_('یادداشت'))

