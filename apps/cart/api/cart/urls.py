from django.urls import path
from apps.cart.api.cart.cart_apis import (
    CartCurrentAPIView,
    CartTotalAPIView,
    CartClearAPIView
)

urlpatterns = [
    path('current/', CartCurrentAPIView.as_view(), name='cart-current'),
    path('total/', CartTotalAPIView.as_view(), name='cart-total'),
    path('clear/', CartClearAPIView.as_view(), name='cart-clear'),
]

