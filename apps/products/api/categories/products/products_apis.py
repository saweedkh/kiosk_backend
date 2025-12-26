from rest_framework import generics
from rest_framework.response import Response
from apps.products.models import Category
from apps.products.api.categories.products.products_serializers import CategoryProductSerializer
from apps.products.selectors.category_selector import CategorySelector


class CategoryProductsAPIView(generics.GenericAPIView):
    serializer_class = CategoryProductSerializer
    
    def get(self, request, pk):
        category = Category.objects.get(pk=pk)
        products = CategorySelector.get_category_products(category.id)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

