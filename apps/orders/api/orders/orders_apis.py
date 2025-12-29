from rest_framework import generics, status
from rest_framework.response import Response
from apps.orders.api.orders.orders_serializers import (
    OrderSerializer,
    OrderCreateSerializer
)
from apps.orders.services.order_service import OrderService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.schema import ResponseStatusCodes


class OrderCreateAPIView(generics.GenericAPIView):
    """
    API endpoint for creating order from frontend items.
    
    Creates an order from items data sent from frontend.
    Stock will be decreased only after payment is completed.
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
        summary="Create Order",
        description="Create an order from items data sent from frontend. Stock will be decreased only after payment is completed.",
        tags=["Orders"],
        operation_id="orders_create",
    )
    def post(self, request):
        """
        Create order from frontend items.
        
        Args:
            request: HTTP request object with items data
            
        Returns:
            Response: Created order data
            
        Raises:
            ValidationError: If items data is invalid
            ValueError: If items list is empty or product not found
            InsufficientStockException: If insufficient stock for any item
        """
        request_serializer = OrderCreateSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_data = request_serializer.validated_data
        
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        order = OrderService.create_order_from_items(session_key, request_data['items'])
        
        return Response(
            data=OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

