from rest_framework import generics
from apps.products.models import Category
from apps.products.api.categories.id.categories_id_serializers import CategorySerializer
from apps.products.selectors.category_selector import CategorySelector


class CategoryRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        return CategorySelector.get_active_categories()

