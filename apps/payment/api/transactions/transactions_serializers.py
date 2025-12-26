from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.payment.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'order_id', 'order_details', 'amount',
            'status', 'payment_method', 'gateway_name', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'order_details', 'status',
            'gateway_name', 'error_message', 'created_at', 'updated_at'
        ]


class TransactionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'order_id', 'amount', 'status',
            'gateway_name', 'created_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'status', 'gateway_name', 'created_at']

