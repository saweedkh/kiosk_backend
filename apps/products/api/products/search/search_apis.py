from rest_framework import generics
from rest_framework.response import Response
from apps.products.api.products.search.search_serializers import ProductSearchSerializer
from apps.products.selectors.product_selector import ProductSelector


class ProductSearchAPIView(generics.GenericAPIView):
    serializer_class = ProductSearchSerializer
    
    def get(self, request):
        query = request.query_params.get('q', '')
        products = ProductSelector.search_products(query)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

