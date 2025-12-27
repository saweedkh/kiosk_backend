from rest_framework import generics
from apps.payment.models import Transaction
from apps.payment.api.transactions.transactions_serializers import (
    TransactionSerializer,
    TransactionListSerializer
)
from apps.payment.api.transactions.transactions_filters import TransactionFilter
from apps.payment.selectors.transaction_selector import TransactionSelector
from apps.core.api.schema import custom_extend_schema
from apps.core.api.parameter_serializers import TransactionQuerySerializer, TransactionPathSerializer
from apps.core.api.status_codes import ResponseStatusCodes


class TransactionListAPIView(generics.ListAPIView):
    """
    API endpoint for listing payment transactions.
    
    Returns transactions filtered by order_id if provided, otherwise all transactions.
    Supports filtering by status, gateway, and date range.
    """
    serializer_class = TransactionListSerializer
    filterset_class = TransactionFilter
    
    @custom_extend_schema(
        resource_name="TransactionList",
        parameters=[TransactionQuerySerializer],
        response_serializer=TransactionListSerializer,
        status_codes=[ResponseStatusCodes.OK_PAGINATED],
        summary="List Transactions",
        description="Get a list of payment transactions. Supports filtering by order_id, status, and gateway.",
        tags=["Transactions"],
        operation_id="transactions_list",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get queryset of transactions.
        
        Query Parameters:
            order_id: Filter transactions by order ID (optional)
            
        Returns:
            QuerySet: QuerySet of transactions
        """
        session_key = self.request.session.session_key
        if not session_key:
            return Transaction.objects.none()
        
        order_id = self.request.query_params.get('order_id')
        if order_id:
            return TransactionSelector.get_transactions_by_order(order_id)
        
        return Transaction.objects.all()


class TransactionRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single transaction by ID.
    
    Returns detailed information about a specific payment transaction.
    """
    serializer_class = TransactionSerializer
    lookup_field = 'pk'
    
    @custom_extend_schema(
        resource_name="TransactionRetrieve",
        parameters=[TransactionPathSerializer],
        response_serializer=TransactionSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.NOT_FOUND,
        ],
        summary="Get Transaction Details",
        description="Retrieve detailed information about a specific payment transaction.",
        tags=["Transactions"],
        operation_id="transactions_retrieve",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get queryset of all transactions.
        
        Returns:
            QuerySet: QuerySet of all transactions
        """
        return Transaction.objects.all()

