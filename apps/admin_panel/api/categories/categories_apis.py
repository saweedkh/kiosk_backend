from rest_framework import generics
from apps.products.models import Category
from apps.admin_panel.api.categories.categories_serializers import (
    AdminCategorySerializer,
    AdminCategoryListSerializer
)
from apps.admin_panel.api.categories.categories_filters import AdminCategoryFilter
from apps.admin_panel.api.permissions import IsAdminUser


class AdminCategoryListAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.select_related('parent').prefetch_related('children').all()
    permission_classes = [IsAdminUser]
    filterset_class = AdminCategoryFilter
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AdminCategoryListSerializer
        return AdminCategorySerializer


class AdminCategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.select_related('parent').prefetch_related('children').all()
    serializer_class = AdminCategorySerializer
    permission_classes = [IsAdminUser]

