from rest_framework import generics
from apps.products.models import Product
from apps.products.api.products.products_serializers import ProductListSerializer
from apps.products.api.products.products_filters import ProductFilter
from apps.products.selectors.product_selector import ProductSelector


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.none()
    serializer_class = ProductListSerializer
    filterset_class = ProductFilter
    
    def get_queryset(self):
        return ProductSelector.get_active_products()
