from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.products.models import Category, Product


class ProductUpdateSerializerInput(serializers.Serializer):
    name = serializers.CharField(required=False, label=_('نام'))
    description = serializers.CharField(required=False, label=_('توضیحات'))
    price = serializers.IntegerField(required=False, label=_('قیمت'))
    category = serializers.PrimaryKeyRelatedField(required=False, queryset=Category.objects.filter(is_active=True), label=_('دسته‌بندی'))
    image = serializers.ImageField(required=False, label=_('تصویر'))
    stock_quantity = serializers.IntegerField(required=False, label=_('موجودی'))
    is_active = serializers.BooleanField(required=False, label=_('فعال'))

class AdminProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, label=_('نام دسته‌بندی'))
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category', 'category_name',
            'image', 'stock_quantity', 'is_active',
            'is_in_stock', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_in_stock', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            request = self.context.get('request')
            if request:
                representation['image'] = request.build_absolute_uri(instance.image.url)
            else:
                representation['image'] = instance.image.url
        return representation


class AdminProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, label=_('نام دسته‌بندی'))
    
    class Meta:
        
        model = Product
        fields = [
            'id', 'name', 'price', 'category_name', 'stock_quantity',
            'is_active', 'is_in_stock'
        ]
        read_only_fields = ['id', 'is_in_stock']


class UpdateStockSerializer(serializers.Serializer):
    stock_quantity = serializers.IntegerField(min_value=0, label=_('موجودی'))
    notes = serializers.CharField(required=False, allow_blank=True, label=_('یادداشت'))

