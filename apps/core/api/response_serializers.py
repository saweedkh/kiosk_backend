from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class ErrorDetailSerializer(serializers.Serializer):
    """
    Standard error detail serializer.
    """
    error = serializers.CharField(help_text=_('Error message'))
    detail = serializers.CharField(help_text=_('Detailed error description'))
    code = serializers.CharField(help_text=_('Error code'))


class BadRequestErrorSerializer(ErrorDetailSerializer):
    """
    Error response serializer for 400 Bad Request.
    """
    pass


class UnauthorizedErrorSerializer(ErrorDetailSerializer):
    """
    Error response serializer for 401 Unauthorized.
    """
    pass


class ForbiddenErrorSerializer(ErrorDetailSerializer):
    """
    Error response serializer for 403 Forbidden.
    """
    pass


class NotFoundErrorSerializer(ErrorDetailSerializer):
    """
    Error response serializer for 404 Not Found.
    """
    pass


class InternalServerErrorSerializer(ErrorDetailSerializer):
    """
    Error response serializer for 500 Internal Server Error.
    """
    pass


class ServiceUnavailableErrorSerializer(ErrorDetailSerializer):
    """
    Error response serializer for 503 Service Unavailable.
    """
    pass


class ValidationErrorSerializer(serializers.Serializer):
    """
    Error response serializer for validation errors (400).
    """
    error = serializers.CharField(help_text=_('Validation error message'))
    detail = serializers.DictField(
        help_text=_('Field-specific validation errors'),
        child=serializers.ListField(child=serializers.CharField())
    )
    code = serializers.CharField(default='validation_error', help_text=_('Error code'))


class OrderNotFoundErrorSerializer(NotFoundErrorSerializer):
    """
    Error response serializer for order not found (404).
    """
    error = serializers.CharField(default='Order not found', help_text=_('Error message'))
    code = serializers.CharField(default='ORDER_NOT_FOUND', help_text=_('Error code'))


class ProductNotFoundErrorSerializer(NotFoundErrorSerializer):
    """
    Error response serializer for product not found (404).
    """
    error = serializers.CharField(default='Product not found', help_text=_('Error message'))
    code = serializers.CharField(default='PRODUCT_NOT_FOUND', help_text=_('Error code'))


class CategoryNotFoundErrorSerializer(NotFoundErrorSerializer):
    """
    Error response serializer for category not found (404).
    """
    error = serializers.CharField(default='Category not found', help_text=_('Error message'))
    code = serializers.CharField(default='CATEGORY_NOT_FOUND', help_text=_('Error code'))


class CartItemNotFoundErrorSerializer(NotFoundErrorSerializer):
    """
    Error response serializer for cart item not found (404).
    """
    error = serializers.CharField(default='Cart item not found', help_text=_('Error message'))
    code = serializers.CharField(default='CART_ITEM_NOT_FOUND', help_text=_('Error code'))


class InvoiceNotFoundErrorSerializer(NotFoundErrorSerializer):
    """
    Error response serializer for invoice not found (404).
    """
    error = serializers.CharField(default='Invoice not found', help_text=_('Error message'))
    code = serializers.CharField(default='INVOICE_NOT_FOUND', help_text=_('Error code'))


class TransactionNotFoundErrorSerializer(NotFoundErrorSerializer):
    """
    Error response serializer for transaction not found (404).
    """
    error = serializers.CharField(default='Transaction not found', help_text=_('Error message'))
    code = serializers.CharField(default='TRANSACTION_NOT_FOUND', help_text=_('Error code'))


class PaymentGatewayErrorSerializer(ServiceUnavailableErrorSerializer):
    """
    Error response serializer for payment gateway errors (503).
    """
    error = serializers.CharField(default='Payment gateway is not active', help_text=_('Error message'))
    code = serializers.CharField(default='PAYMENT_GATEWAY_ERROR', help_text=_('Error code'))


class PaymentFailedErrorSerializer(InternalServerErrorSerializer):
    """
    Error response serializer for payment failures (500).
    """
    error = serializers.CharField(default='Payment failed', help_text=_('Error message'))
    code = serializers.CharField(default='PAYMENT_FAILED', help_text=_('Error code'))


class InsufficientStockErrorSerializer(BadRequestErrorSerializer):
    """
    Error response serializer for insufficient stock (400).
    """
    error = serializers.CharField(default='Insufficient stock', help_text=_('Error message'))
    code = serializers.CharField(default='INSUFFICIENT_STOCK', help_text=_('Error code'))


class EmptyCartErrorSerializer(BadRequestErrorSerializer):
    """
    Error response serializer for empty cart (400).
    """
    error = serializers.CharField(default='Cart is empty', help_text=_('Error message'))
    code = serializers.CharField(default='EMPTY_CART', help_text=_('Error code'))


class UnauthorizedAccessErrorSerializer(UnauthorizedErrorSerializer):
    """
    Error response serializer for unauthorized access (401).
    """
    error = serializers.CharField(default='Authentication required', help_text=_('Error message'))
    code = serializers.CharField(default='UNAUTHORIZED', help_text=_('Error code'))


class ForbiddenAccessErrorSerializer(ForbiddenErrorSerializer):
    """
    Error response serializer for forbidden access (403).
    """
    error = serializers.CharField(default='You do not have permission to perform this action', help_text=_('Error message'))
    code = serializers.CharField(default='FORBIDDEN', help_text=_('Error code'))


class SuccessMessageSerializer(serializers.Serializer):
    """
    Success response serializer with message.
    """
    message = serializers.CharField(help_text=_('Success message'))
    data = serializers.DictField(required=False, help_text=_('Additional data'))


class CreatedResponseSerializer(serializers.Serializer):
    """
    Standard 201 Created response serializer.
    """
    id = serializers.IntegerField(help_text=_('Created resource ID'))
    message = serializers.CharField(default='Created successfully', help_text=_('Success message'))


class NoContentResponseSerializer(serializers.Serializer):
    """
    Standard 204 No Content response serializer.
    """
    pass

