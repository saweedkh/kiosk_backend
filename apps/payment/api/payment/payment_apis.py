from rest_framework import generics, status
from rest_framework.response import Response
from apps.payment.api.payment.payment_serializers import (
    PaymentInitiateSerializer,
    PaymentVerifySerializer,
    PaymentStatusSerializer,
    PaymentResponseSerializer
)
from apps.payment.services.payment_service import PaymentService
from apps.orders.selectors.order_selector import OrderSelector
from apps.orders.services.invoice_service import InvoiceService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.schema import ResponseStatusCodes


class PaymentInitiateAPIView(generics.GenericAPIView):
    """
    API endpoint for initiating payment transaction.
    
    Initiates a payment transaction with the payment gateway for an order.
    """
    serializer_class = PaymentInitiateSerializer
    
    @custom_extend_schema(
        resource_name="PaymentInitiate",
        parameters=[PaymentInitiateSerializer],
        response_serializer=PaymentResponseSerializer,
        status_codes=[
            ResponseStatusCodes.CREATED,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.SERVER_ERROR,
        ],
        summary="Initiate Payment",
        description="Initiate a payment transaction with the payment gateway for an order. Returns transaction details including transaction ID.",
        tags=["Payment"],
        operation_id="payment_initiate"
    )
    def post(self, request):
        """
        Initiate payment for an order.
        
        Args:
            request: HTTP request object with order_id and amount
            
        Returns:
            Response: Transaction data with status
            
        Raises:
            404: If order not found
            GatewayException: If payment gateway is not active
            PaymentFailedException: If payment initiation fails
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        amount = serializer.validated_data['amount']
        
        order = OrderSelector.get_order_by_id(order_id)
        if not order:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        order_details = InvoiceService.get_invoice_data(order_id)
        
        transaction = PaymentService.initiate_payment(
            order_id=order_id,
            amount=amount,
            order_details=order_details
        )
        
        order.transaction_id = transaction.transaction_id
        order.payment_status = 'processing'
        order.save()
        
        return Response(
            PaymentResponseSerializer(transaction).data,
            status=status.HTTP_201_CREATED
        )


class PaymentVerifyAPIView(generics.GenericAPIView):
    """
    API endpoint for verifying payment transaction.
    
    Verifies a payment transaction with the payment gateway and updates order status.
    """
    serializer_class = PaymentVerifySerializer
    
    @custom_extend_schema(
        resource_name="PaymentVerify",
        parameters=[PaymentVerifySerializer],
        response_serializer=PaymentResponseSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.SERVER_ERROR,
        ],
        summary="Verify Payment",
        description="Verify a payment transaction with the payment gateway. Updates order status based on verification result.",
        tags=["Payment"],
        operation_id="payment_verify"
    )
    def post(self, request):
        """
        Verify payment transaction.
        
        Args:
            request: HTTP request object with transaction_id
            
        Returns:
            Response: Verified transaction data
            
        Raises:
            GatewayException: If transaction not found
            PaymentFailedException: If payment verification fails
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        transaction_id = serializer.validated_data['transaction_id']
        
        transaction = PaymentService.verify_payment(transaction_id)
        
        if transaction.order_id:
            order = OrderSelector.get_order_by_id(transaction.order_id)
            if order:
                if transaction.status == 'success':
                    # Update order payment status and decrease stock
                    from apps.orders.services.order_service import OrderService
                    OrderService.update_payment_status(order.id, 'paid')
                elif transaction.status == 'failed':
                    order.payment_status = 'failed'
                    order.save()
        
        return Response(PaymentResponseSerializer(transaction).data)


class PaymentStatusAPIView(generics.GenericAPIView):
    """
    API endpoint for checking payment status.
    
    Gets the current payment status from the payment gateway.
    """
    serializer_class = PaymentStatusSerializer
    
    @custom_extend_schema(
        resource_name="PaymentStatus",
        parameters=[PaymentStatusSerializer],
        response_serializer=PaymentResponseSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.SERVER_ERROR,
        ],
        summary="Get Payment Status",
        description="Get the current payment status from the payment gateway for a transaction.",
        tags=["Payment"],
        operation_id="payment_status"
    )
    def post(self, request):
        """
        Get payment status.
        
        Args:
            request: HTTP request object with transaction_id
            
        Returns:
            Response: Transaction status data
            
        Raises:
            GatewayException: If transaction not found or status check fails
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        transaction_id = serializer.validated_data['transaction_id']
        
        transaction = PaymentService.get_payment_status(transaction_id)
        
        return Response(PaymentResponseSerializer(transaction).data)

