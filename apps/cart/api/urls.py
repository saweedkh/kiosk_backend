from django.urls import path, include

app_name = 'cart'

urlpatterns = [
    path('cart/', include('apps.cart.api.cart.urls')),
    path('cart-items/', include('apps.cart.api.cart_items.urls')),
]

