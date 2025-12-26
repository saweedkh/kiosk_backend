from django.urls import path
from apps.admin_panel.api.categories.categories_apis import (
    AdminCategoryListAPIView,
    AdminCategoryRetrieveUpdateDestroyAPIView
)

urlpatterns = [
    path('', AdminCategoryListAPIView.as_view(), name='admin-category-list'),
    path('<int:pk>/', AdminCategoryRetrieveUpdateDestroyAPIView.as_view(), name='admin-category-detail'),
]

