from typing import Optional, List, Dict, Tuple
from django.db import transaction
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.orders.selectors.order_selector import OrderSelector
from apps.products.models import Product
from apps.products.services.stock_service import StockService
from apps.logs.services.log_service import LogService
from apps.core.exceptions.order import OrderNotFoundException
from apps.core.exceptions.order import InsufficientStockException
from apps.payment.gateway.adapter import PaymentGatewayAdapter
from apps.payment.gateway.exceptions import GatewayException
from apps.payment.services.payment_service import PaymentService


class OrderService:
    """
    Order management service.
    
    This class contains all business logic related to order processing.
    """
    
    @staticmethod
    def generate_order_number() -> str:
        """
        Generate unique order number.
        
        Format: ORD-YYYYMMDDHHMMSS-XXXX
        Where XXXX is microsecond suffix for uniqueness.
        
        Returns:
            str: Unique order number
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(timezone.now().microsecond)[:4]
        return f"ORD-{timestamp}-{random_suffix}"
    
    @staticmethod
    @transaction.atomic
    def create_order_from_items(session_key: str, items: List[Dict], process_payment: bool = True) -> Order:
        """
        Create order from items data sent from frontend and process payment directly.
        
        This method creates an order from items data, validates stock availability,
        and immediately processes payment through POS device. If payment is successful,
        stock is decreased and order status is updated to 'paid'.
        
        Args:
            session_key: Django session key
            items: List of order items with product_id and quantity
            process_payment: If True, payment will be processed immediately via POS
            
        Returns:
            Order: Created order with payment information
            
        Raises:
            ValueError: If items list is empty or product not found
            InsufficientStockException: If insufficient stock for any item
            GatewayException: If payment gateway is not active or payment fails
        """
        if not items:
            raise ValueError('Items list is empty')
        
        order_number = OrderService.generate_order_number()
        total_amount = 0
        
        # Validate products and calculate total
        order_items_data = []
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                raise ValueError(f'Product with id {product_id} does not exist or is not active')
            
            # Check stock availability
            if product.stock_quantity < quantity:
                raise InsufficientStockException(
                    f'Insufficient stock for product {product.name}. '
                    f'Available: {product.stock_quantity}, Requested: {quantity}'
                )
            
            # Use product price as unit_price
            unit_price = product.price
            total_amount += quantity * unit_price
            order_items_data.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price
            })
        
        # Create order
        order = Order.objects.create(
            order_number=order_number,
            session_key=session_key,
            status='pending',
            total_amount=total_amount,
            payment_status='pending'
        )
        
        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            )
        
        LogService.log_info(
            'order',
            'order_created',
            details={
                'order_id': order.id,
                'order_number': order_number,
                'session_key': session_key,
                'total_amount': total_amount
            }
        )
        
        # Process payment immediately if requested
        if process_payment:
            try:
                # Check if gateway is active
                if not PaymentGatewayAdapter.is_gateway_active():
                    raise GatewayException('Payment gateway is not active')
                
                gateway = PaymentGatewayAdapter.get_gateway()
                
                # Prepare order details for payment
                order_details = {
                    'order_number': order_number,
                    'order_id': order.id,
                }
                
                # Initiate payment through gateway (this will send to POS device)
                gateway_response = gateway.initiate_payment(
                    amount=total_amount,
                    order_details=order_details
                )
                
                # Debug: Log gateway response
                LogService.log_info(
                    'payment',
                    'gateway_response_received',
                    details={
                        'order_id': order.id,
                        'gateway_response': gateway_response,
                        'success': gateway_response.get('success'),
                        'status': gateway_response.get('status')
                    }
                )
                
                # Generate transaction ID
                transaction_id = PaymentService.generate_transaction_id()
                
                # Determine payment status from gateway response
                # Check both 'success' field and 'status' field
                payment_success = gateway_response.get('success', False)
                gateway_status = gateway_response.get('status', '')
                
                # If gateway returns status='success', consider it successful
                if gateway_status == 'success':
                    payment_success = True
                
                payment_status = 'success' if payment_success else 'failed'
                
                LogService.log_info(
                    'payment',
                    'payment_status_determined',
                    details={
                        'order_id': order.id,
                        'payment_success': payment_success,
                        'payment_status': payment_status,
                        'gateway_status': gateway_status
                    }
                )
                
                # Update order with payment/transaction information
                order.transaction_id = transaction_id
                order.gateway_name = gateway.__class__.__name__
                order.gateway_request_data = {'amount': total_amount, 'order_details': order_details}
                order.gateway_response_data = gateway_response
                order.order_details = order_details
                
                # If payment successful, update order status and decrease stock
                if payment_success:
                    order.payment_status = 'paid'
                    updated_order = OrderService.update_payment_status(order.id, 'paid')
                    # Refresh order object to get latest status
                    order.refresh_from_db()
                    LogService.log_info(
                        'payment',
                        'payment_completed',
                        details={
                            'transaction_id': transaction_id,
                            'order_id': order.id,
                            'order_number': order_number,
                            'amount': total_amount
                        }
                    )
                else:
                    # Payment failed - update order status
                    order.payment_status = 'failed'
                    order.status = 'cancelled'
                    error_message = gateway_response.get('response_message', 'Payment failed')
                    order.error_message = error_message
                    order.save()
                    
                    LogService.log_error(
                        'payment',
                        'payment_failed',
                        details={
                            'transaction_id': transaction_id,
                            'order_id': order.id,
                            'order_number': order_number,
                            'amount': total_amount,
                            'error': error_message
                        }
                    )
                    
                    raise GatewayException(f'Payment failed: {error_message}')
                
            except GatewayException:
                # Re-raise gateway exceptions
                raise
            except Exception as e:
                # Log unexpected errors
                LogService.log_error(
                    'payment',
                    'payment_processing_error',
                    details={
                        'order_id': order.id,
                        'order_number': order_number,
                        'amount': total_amount,
                        'error': str(e)
                    }
                )
                # Mark order as failed
                order.payment_status = 'failed'
                order.status = 'cancelled'
                order.error_message = str(e)
                order.save()
                raise GatewayException(f'Failed to process payment: {str(e)}')
        
        return order
    
    @staticmethod
    @transaction.atomic
    def update_order_status(order_id: int, status: str) -> Order:
        """
        Update order status.
        
        Args:
            order_id: Order ID
            status: New status (e.g., 'pending', 'processing', 'completed', 'cancelled')
            
        Returns:
            Order: Updated order instance
            
        Raises:
            OrderNotFoundException: If order does not exist
        """
        order = OrderSelector.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundException()
        
        old_status = order.status
        order.status = status
        order.save()
        
        LogService.log_info(
            'order',
            'order_status_updated',
            details={
                'order_id': order.id,
                'order_number': order.order_number,
                'old_status': old_status,
                'new_status': status
            }
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def update_payment_status(order_id: int, payment_status: str) -> Order:
        """
        Update order payment status.
        
        If payment_status is 'paid', order status is also set to 'paid' and stock is decreased.
        
        Args:
            order_id: Order ID
            payment_status: New payment status (e.g., 'pending', 'paid', 'failed')
            
        Returns:
            Order: Updated order instance
            
        Raises:
            OrderNotFoundException: If order does not exist
            InsufficientStockException: If insufficient stock when trying to complete payment
        """
        order = OrderSelector.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundException()
        
        old_payment_status = order.payment_status
        old_status = order.status
        
        # If payment is being completed, decrease stock
        if payment_status == 'paid' and old_payment_status != 'paid':
            # Validate stock availability before decreasing
            for order_item in order.items.all():
                if order_item.product.stock_quantity < order_item.quantity:
                    raise InsufficientStockException(
                        f'Insufficient stock for product {order_item.product.name}. '
                        f'Available: {order_item.product.stock_quantity}, Requested: {order_item.quantity}'
                    )
            
            # Decrease stock for all order items
            for order_item in order.items.all():
                StockService.decrease_stock(
                    product_id=order_item.product_id,
                    quantity=order_item.quantity,
                    related_order_id=order.id
                )
            
            order.status = 'paid'
        
        order.payment_status = payment_status
        order.save()
        
        LogService.log_info(
            'order',
            'payment_status_updated',
            details={
                'order_id': order.id,
                'order_number': order.order_number,
                'old_payment_status': old_payment_status,
                'new_payment_status': payment_status,
                'old_status': old_status,
                'new_status': order.status
            }
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order_id: int) -> Order:
        """
        Cancel order and restore stock quantities if payment was completed.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Order: Cancelled order instance
            
        Raises:
            OrderNotFoundException: If order does not exist
            ValueError: If order status is 'completed' or 'cancelled'
        """
        order = OrderSelector.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundException()
        
        if order.status in ['completed', 'cancelled']:
            raise ValueError(f'Cannot cancel order with status: {order.status}')
        
        # Only restore stock if payment was completed (stock was decreased)
        if order.payment_status == 'paid':
            for order_item in order.items.all():
                StockService.increase_stock(
                    product_id=order_item.product_id,
                    quantity=order_item.quantity,
                    notes=f'Order {order.order_number} cancelled'
                )
        
        order.status = 'cancelled'
        order.save()
        
        LogService.log_info(
            'order',
            'order_cancelled',
            details={
                'order_id': order.id,
                'order_number': order.order_number,
                'payment_status': order.payment_status
            }
        )
        
        return order

