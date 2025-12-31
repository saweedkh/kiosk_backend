from rest_framework import generics, status
from rest_framework.response import Response
from apps.orders.api.orders.orders_serializers import (
    OrderSerializer,
    OrderCreateSerializer
)
from apps.orders.services.order_service import OrderService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.schema import ResponseStatusCodes
from apps.payment.gateway.exceptions import GatewayException
from apps.core.exceptions.payment import PaymentFailedException


class OrderCreateAPIView(generics.GenericAPIView):
    """
    API endpoint for creating order from frontend items.
    
    Creates an order from items data sent from frontend and processes payment
    directly through POS device. If payment is successful, stock is decreased
    and order status is updated to 'paid'.
    """
    serializer_class = OrderCreateSerializer
    
    @custom_extend_schema(
        resource_name="OrderCreate",
        parameters=[OrderCreateSerializer],
        response_serializer=OrderSerializer,
        status_codes=[
            ResponseStatusCodes.CREATED,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.SERVER_ERROR,
        ],
        summary="Create Order and Process Payment",
        description="Create an order from items data and process payment directly through POS device. Payment is processed immediately and stock is decreased if payment is successful.",
        tags=["Orders"],
        operation_id="orders_create",
    )
    def post(self, request):
        """
        Create order from frontend items and process payment.
        
        This endpoint:
        1. Creates order from items
        2. Immediately processes payment through POS device
        3. Decreases stock if payment is successful
        4. Updates order status based on payment result
        
        Args:
            request: HTTP request object with items data
            
        Returns:
            Response: Created order data with payment status
            
        Raises:
            ValidationError: If items data is invalid
            ValueError: If items list is empty or product not found
            InsufficientStockException: If insufficient stock for any item
            GatewayException: If payment gateway is not active or payment fails
        """
        request_serializer = OrderCreateSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_data = request_serializer.validated_data
        
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        try:
            order, transaction = OrderService.create_order_from_items(
                session_key, 
                request_data['items'],
                process_payment=True
            )
            
            response_data = OrderSerializer(order).data
            
            # Add payment information to response
            if transaction:
                response_data['payment'] = {
                    'transaction_id': transaction.transaction_id,
                    'status': transaction.status,
                    'gateway_name': transaction.gateway_name
                }
            
            return Response(
                data=response_data,
                status=status.HTTP_201_CREATED
            )
            
        except GatewayException as e:
            # Payment failed - return error with order details if order was created
            error_response = {
                'error': 'Payment failed',
                'message': str(e)
            }
            
            # Try to get order if it was created before payment failed
            # (order might be in cancelled state)
            if 'order' in locals():
                error_response['order'] = OrderSerializer(order).data
            
            return Response(
                data=error_response,
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        except PaymentFailedException as e:
            return Response(
                data={
                    'error': 'Payment processing failed',
                    'message': str(e)
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

