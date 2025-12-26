from django.urls import path
from apps.admin_panel.api.products.products_apis import (
    AdminProductListAPIView,
    AdminProductRetrieveUpdateDestroyAPIView,
    AdminProductUpdateStockAPIView
)

urlpatterns = [
    path('', AdminProductListAPIView.as_view(), name='admin-product-list'),
    path('<int:pk>/', AdminProductRetrieveUpdateDestroyAPIView.as_view(), name='admin-product-detail'),
    path('<int:pk>/update-stock/', AdminProductUpdateStockAPIView.as_view(), name='admin-product-update-stock'),
]

