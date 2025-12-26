from rest_framework import generics
from apps.products.models import Product
from apps.products.api.products.id.products_id_serializers import ProductDetailSerializer
from apps.products.selectors.product_selector import ProductSelector


class ProductRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        return ProductSelector.get_active_products()

