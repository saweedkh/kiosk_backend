from django.urls import path
from apps.orders.api.orders.orders_apis import (
    OrderListAPIView,
    OrderCreateAPIView,
    OrderRetrieveAPIView
)

urlpatterns = [
    path('', OrderListAPIView.as_view(), name='order-list'),
    path('create/', OrderCreateAPIView.as_view(), name='order-create'),
    path('<int:pk>/', OrderRetrieveAPIView.as_view(), name='order-retrieve'),
]

