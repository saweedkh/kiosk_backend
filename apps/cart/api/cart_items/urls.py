from django.urls import path
from apps.cart.api.cart_items.cart_items_apis import (
    CartItemListAPIView,
    CartItemCreateAPIView,
    CartItemUpdateAPIView,
    CartItemDeleteAPIView
)

urlpatterns = [
    path('', CartItemListAPIView.as_view(), name='cart-item-list'),
    path('create/', CartItemCreateAPIView.as_view(), name='cart-item-create'),
    path('<int:pk>/update/', CartItemUpdateAPIView.as_view(), name='cart-item-update'),
    path('<int:pk>/delete/', CartItemDeleteAPIView.as_view(), name='cart-item-delete'),
]

