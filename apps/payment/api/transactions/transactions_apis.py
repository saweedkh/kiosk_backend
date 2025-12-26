from rest_framework import generics
from apps.payment.models import Transaction
from apps.payment.api.transactions.transactions_serializers import (
    TransactionSerializer,
    TransactionListSerializer
)
from apps.payment.api.transactions.transactions_filters import TransactionFilter
from apps.payment.selectors.transaction_selector import TransactionSelector


class TransactionListAPIView(generics.ListAPIView):
    serializer_class = TransactionListSerializer
    filterset_class = TransactionFilter
    
    def get_queryset(self):
        session_key = self.request.session.session_key
        if not session_key:
            return Transaction.objects.none()
        
        order_id = self.request.query_params.get('order_id')
        if order_id:
            return TransactionSelector.get_transactions_by_order(order_id)
        
        return Transaction.objects.all()


class TransactionRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Transaction.objects.all()

