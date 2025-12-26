from django.urls import path
from apps.admin_panel.api.orders.orders_apis import (
    AdminOrderListAPIView,
    AdminOrderRetrieveAPIView,
    AdminOrderUpdateStatusAPIView
)

urlpatterns = [
    path('', AdminOrderListAPIView.as_view(), name='admin-order-list'),
    path('<int:pk>/', AdminOrderRetrieveAPIView.as_view(), name='admin-order-retrieve'),
    path('<int:pk>/update-status/', AdminOrderUpdateStatusAPIView.as_view(), name='admin-order-update-status'),
]

