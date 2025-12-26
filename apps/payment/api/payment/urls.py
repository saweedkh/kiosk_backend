from django.urls import path
from apps.payment.api.payment.payment_apis import (
    PaymentInitiateAPIView,
    PaymentVerifyAPIView,
    PaymentStatusAPIView
)

urlpatterns = [
    path('initiate/', PaymentInitiateAPIView.as_view(), name='payment-initiate'),
    path('verify/', PaymentVerifyAPIView.as_view(), name='payment-verify'),
    path('status/', PaymentStatusAPIView.as_view(), name='payment-status'),
]

