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


class PaymentInitiateAPIView(generics.GenericAPIView):
    serializer_class = PaymentInitiateSerializer
    
    def post(self, request):
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
    serializer_class = PaymentVerifySerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        transaction_id = serializer.validated_data['transaction_id']
        
        transaction = PaymentService.verify_payment(transaction_id)
        
        if transaction.order_id:
            order = OrderSelector.get_order_by_id(transaction.order_id)
            if order:
                if transaction.status == 'success':
                    order.payment_status = 'paid'
                    order.status = 'paid'
                elif transaction.status == 'failed':
                    order.payment_status = 'failed'
                order.save()
        
        return Response(PaymentResponseSerializer(transaction).data)


class PaymentStatusAPIView(generics.GenericAPIView):
    serializer_class = PaymentStatusSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        transaction_id = serializer.validated_data['transaction_id']
        
        transaction = PaymentService.get_payment_status(transaction_id)
        
        return Response(PaymentResponseSerializer(transaction).data)

