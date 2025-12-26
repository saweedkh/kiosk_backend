from rest_framework import generics
from apps.products.models import Category
from apps.products.api.categories.categories_serializers import CategoryListSerializer
from apps.products.selectors.category_selector import CategorySelector


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.none()
    serializer_class = CategoryListSerializer
    
    def get_queryset(self):
        return CategorySelector.get_active_categories()

