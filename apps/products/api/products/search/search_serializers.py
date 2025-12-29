from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.products.models import Product


class ProductSearchQuerySerializer(serializers.Serializer):
    """Serializer for product search query parameters."""
    q = serializers.CharField(required=True, label=_('جستجو'), help_text=_('Search query string'))


class ProductSearchSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True,
        label=_('نام دسته‌بندی')
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'category_name',
            'image', 'stock_quantity', 'is_in_stock'
        ]

