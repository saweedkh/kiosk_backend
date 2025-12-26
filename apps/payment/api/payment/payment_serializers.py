from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.payment.models import Transaction


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(label=_('شناسه سفارش'))
    amount = serializers.IntegerField(min_value=1, label=_('مبلغ'))


class PaymentVerifySerializer(serializers.Serializer):
    transaction_id = serializers.CharField(label=_('شناسه تراکنش'))


class PaymentStatusSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(label=_('شناسه تراکنش'))


class PaymentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'order_id', 'amount', 'status',
            'gateway_name', 'gateway_response_data', 'created_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'status', 'gateway_name', 'gateway_response_data', 'created_at']

