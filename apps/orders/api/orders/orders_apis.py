from rest_framework import generics, status
from rest_framework.response import Response
from apps.orders.models import Order
from apps.orders.api.orders.orders_serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderCreateSerializer
)
from apps.orders.selectors.order_selector import OrderSelector
from apps.orders.services.order_service import OrderService
from apps.core.api.schema import custom_extend_schema
from apps.core.api.parameter_serializers import OrderPathSerializer
from apps.core.api.status_codes import ResponseStatusCodes


class OrderListAPIView(generics.ListAPIView):
    """
    API endpoint for listing orders.
    
    Returns all orders for the current session.
    """
    serializer_class = OrderListSerializer
    
    @custom_extend_schema(
        resource_name="OrderList",
        response_serializer=OrderListSerializer,
        status_codes=[ResponseStatusCodes.OK_ALL],
        summary="List Orders",
        description="Get all orders for the current session.",
        tags=["Orders"],
        operation_id="orders_list",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get queryset of orders for current session.
        
        Returns:
            QuerySet: QuerySet of orders for the session
        """
        session_key = self.request.session.session_key
        if not session_key:
            return Order.objects.none()
        
        return OrderSelector.get_orders_by_session(session_key)


class OrderCreateAPIView(generics.GenericAPIView):
    """
    API endpoint for creating order from cart.
    
    Creates an order from the current cart items and decreases stock quantities.
    """
    serializer_class = OrderCreateSerializer
    
    @custom_extend_schema(
        resource_name="OrderCreate",
        parameters=[OrderCreateSerializer],
        request_serializer=OrderCreateSerializer,
        response_serializer=OrderSerializer,
        status_codes=[
            ResponseStatusCodes.CREATED,
            ResponseStatusCodes.BAD_REQUEST,
            ResponseStatusCodes.NOT_FOUND,
            ResponseStatusCodes.SERVER_ERROR,
        ],
        summary="Create Order",
        description="Create an order from the current cart items. Decreases stock quantities for ordered items.",
        tags=["Orders"],
        operation_id="orders_create",
    )
    def post(self, request):
        """
        Create order from cart.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Created order data
            
        Raises:
            ValueError: If cart is empty
            InsufficientStockException: If insufficient stock for any item
        """
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        order = OrderService.create_order_from_cart(session_key)
        
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single order by ID.
    
    Returns detailed information about a specific order.
    Only returns orders belonging to the current session.
    """
    serializer_class = OrderSerializer
    lookup_field = 'pk'
    
    @custom_extend_schema(
        resource_name="OrderRetrieve",
        parameters=[OrderPathSerializer],
        response_serializer=OrderSerializer,
        status_codes=[
            ResponseStatusCodes.OK,
            ResponseStatusCodes.NOT_FOUND,
        ],
        summary="Get Order Details",
        description="Retrieve detailed information about a specific order. Only returns orders belonging to the current session.",
        tags=["Orders"],
        operation_id="orders_retrieve",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get queryset of orders for current session.
        
        Returns:
            QuerySet: QuerySet of orders for the session
        """
        session_key = self.request.session.session_key
        if not session_key:
            return Order.objects.none()
        
        return OrderSelector.get_orders_by_session(session_key)

