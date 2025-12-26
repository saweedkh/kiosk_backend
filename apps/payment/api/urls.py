from django.urls import path, include

app_name = 'payment'

urlpatterns = [
    path('payment/', include('apps.payment.api.payment.urls')),
    path('transactions/', include('apps.payment.api.transactions.urls')),
]

