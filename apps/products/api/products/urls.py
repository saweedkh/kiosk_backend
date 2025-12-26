from django.urls import path
from apps.products.api.products.products_apis import ProductListAPIView
from apps.products.api.products.id.products_id_apis import ProductRetrieveAPIView
from apps.products.api.products.search.search_apis import ProductSearchAPIView
from apps.products.api.products.low_stock.low_stock_apis import ProductLowStockAPIView

urlpatterns = [
    path('', ProductListAPIView.as_view(), name='product-list'),
    path('search/', ProductSearchAPIView.as_view(), name='product-search'),
    path('low_stock/', ProductLowStockAPIView.as_view(), name='product-low-stock'),
    path('<int:pk>/', ProductRetrieveAPIView.as_view(), name='product-detail'),
]

