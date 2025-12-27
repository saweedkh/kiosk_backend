from typing import Dict, Any, Type
from rest_framework import serializers
from drf_spectacular.utils import OpenApiResponse
from apps.core.api.response_serializers import (
    BadRequestErrorSerializer,
    UnauthorizedErrorSerializer,
    ForbiddenErrorSerializer,
    NotFoundErrorSerializer,
    InternalServerErrorSerializer,
    ServiceUnavailableErrorSerializer,
    ValidationErrorSerializer,
    OrderNotFoundErrorSerializer,
    ProductNotFoundErrorSerializer,
    CategoryNotFoundErrorSerializer,
    CartItemNotFoundErrorSerializer,
    InvoiceNotFoundErrorSerializer,
    TransactionNotFoundErrorSerializer,
    PaymentGatewayErrorSerializer,
    PaymentFailedErrorSerializer,
    InsufficientStockErrorSerializer,
    EmptyCartErrorSerializer,
    UnauthorizedAccessErrorSerializer,
    ForbiddenAccessErrorSerializer,
)


def get_standard_error_responses(
    include_400: bool = True,
    include_401: bool = True,
    include_403: bool = True,
    include_404: bool = True,
    include_500: bool = True,
    custom_404: Type[serializers.Serializer] = None,
    custom_400: Type[serializers.Serializer] = None,
) -> Dict[int, Any]:
    """
    Get standard error responses for common HTTP status codes.
    
    Args:
        include_400: Include 400 Bad Request response
        include_401: Include 401 Unauthorized response
        include_403: Include 403 Forbidden response
        include_404: Include 404 Not Found response
        include_500: Include 500 Internal Server Error response
        custom_404: Custom 404 error serializer (e.g., OrderNotFoundErrorSerializer)
        custom_400: Custom 400 error serializer (e.g., ValidationErrorSerializer)
        
    Returns:
        Dictionary mapping status codes to response schemas
    """
    responses = {}
    
    if include_400:
        if custom_400:
            responses[400] = OpenApiResponse(
                response=custom_400,
                description="Bad Request - Invalid input data"
            )
        else:
            responses[400] = OpenApiResponse(
                response=BadRequestErrorSerializer,
                description="Bad Request - Invalid input data"
            )
    
    if include_401:
        responses[401] = OpenApiResponse(
            response=UnauthorizedErrorSerializer,
            description="Unauthorized - Authentication required"
        )
    
    if include_403:
        responses[403] = OpenApiResponse(
            response=ForbiddenErrorSerializer,
            description="Forbidden - Insufficient permissions"
        )
    
    if include_404:
        if custom_404:
            responses[404] = OpenApiResponse(
                response=custom_404,
                description="Not Found - Resource not found"
            )
        else:
            responses[404] = OpenApiResponse(
                response=NotFoundErrorSerializer,
                description="Not Found - Resource not found"
            )
    
    if include_500:
        responses[500] = OpenApiResponse(
            response=InternalServerErrorSerializer,
            description="Internal Server Error"
        )
    
    return responses


def get_payment_error_responses() -> Dict[int, Any]:
    """
    Get standard error responses for payment endpoints.
    
    Returns:
        Dictionary mapping status codes to payment-specific error responses
    """
    return {
        400: OpenApiResponse(
            response=BadRequestErrorSerializer,
            description="Bad Request - Invalid input data"
        ),
        404: OpenApiResponse(
            response=TransactionNotFoundErrorSerializer,
            description="Not Found - Transaction not found"
        ),
        500: OpenApiResponse(
            response=PaymentFailedErrorSerializer,
            description="Internal Server Error - Payment processing failed"
        ),
        503: OpenApiResponse(
            response=PaymentGatewayErrorSerializer,
            description="Service Unavailable - Payment gateway is not active"
        ),
    }


def get_order_error_responses() -> Dict[int, Any]:
    """
    Get standard error responses for order endpoints.
    
    Returns:
        Dictionary mapping status codes to order-specific error responses
    """
    return {
        400: OpenApiResponse(
            response=EmptyCartErrorSerializer,
            description="Bad Request - Cart is empty or invalid"
        ),
        404: OpenApiResponse(
            response=OrderNotFoundErrorSerializer,
            description="Not Found - Order not found"
        ),
        500: OpenApiResponse(
            response=InternalServerErrorSerializer,
            description="Internal Server Error - Insufficient stock for one or more items"
        ),
    }


def get_product_error_responses() -> Dict[int, Any]:
    """
    Get standard error responses for product endpoints.
    
    Returns:
        Dictionary mapping status codes to product-specific error responses
    """
    return {
        400: OpenApiResponse(
            response=ValidationErrorSerializer,
            description="Bad Request - Invalid filter parameters"
        ),
        404: OpenApiResponse(
            response=ProductNotFoundErrorSerializer,
            description="Not Found - Product not found"
        ),
    }


def get_category_error_responses() -> Dict[int, Any]:
    """
    Get standard error responses for category endpoints.
    
    Returns:
        Dictionary mapping status codes to category-specific error responses
    """
    return {
        400: OpenApiResponse(
            response=BadRequestErrorSerializer,
            description="Bad Request - Invalid input data"
        ),
        404: OpenApiResponse(
            response=CategoryNotFoundErrorSerializer,
            description="Not Found - Category not found"
        ),
    }


def get_cart_error_responses() -> Dict[int, Any]:
    """
    Get standard error responses for cart endpoints.
    
    Returns:
        Dictionary mapping status codes to cart-specific error responses
    """
    return {
        400: OpenApiResponse(
            response=InsufficientStockErrorSerializer,
            description="Bad Request - Invalid input data or insufficient stock"
        ),
        404: OpenApiResponse(
            response=CartItemNotFoundErrorSerializer,
            description="Not Found - Cart item not found"
        ),
    }


def get_invoice_error_responses() -> Dict[int, Any]:
    """
    Get standard error responses for invoice endpoints.
    
    Returns:
        Dictionary mapping status codes to invoice-specific error responses
    """
    return {
        400: OpenApiResponse(
            response=BadRequestErrorSerializer,
            description="Bad Request - Order not found or invoice already exists"
        ),
        404: OpenApiResponse(
            response=InvoiceNotFoundErrorSerializer,
            description="Not Found - Invoice not found"
        ),
    }


def get_admin_error_responses() -> Dict[int, Any]:
    """
    Get standard error responses for admin endpoints.
    
    Returns:
        Dictionary mapping status codes to admin-specific error responses
    """
    return {
        400: OpenApiResponse(
            response=ValidationErrorSerializer,
            description="Bad Request - Invalid input data"
        ),
        401: OpenApiResponse(
            response=UnauthorizedAccessErrorSerializer,
            description="Unauthorized - Admin authentication required"
        ),
        403: OpenApiResponse(
            response=ForbiddenAccessErrorSerializer,
            description="Forbidden - Admin access required"
        ),
        404: OpenApiResponse(
            response=NotFoundErrorSerializer,
            description="Not Found - Resource not found"
        ),
    }

