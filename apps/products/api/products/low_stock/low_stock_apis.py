from rest_framework import generics
from rest_framework.response import Response
from apps.products.api.products.low_stock.low_stock_serializers import ProductLowStockSerializer
from apps.products.selectors.product_selector import ProductSelector


class ProductLowStockAPIView(generics.GenericAPIView):
    serializer_class = ProductLowStockSerializer
    
    def get(self, request):
        products = ProductSelector.get_low_stock_products()
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

