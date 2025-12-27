from django.urls import path, include
from apps.admin_panel.api.orders.orders_apis import AdminOrderListAPIView

urlpatterns = [
    path('', AdminOrderListAPIView.as_view(), name='admin-order-list'),
    path('<int:pk>/', include('apps.admin_panel.api.orders.id.urls')),
]

