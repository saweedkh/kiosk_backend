from typing import Dict, Any, Type, Union
from rest_framework import serializers
from drf_spectacular.utils import OpenApiResponse
from rest_framework import status
from apps.core.api.status_codes import ResponseStatusCodes
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


def get_status_code_response(
    status_code: Union[int, str],
    serializer: Type[serializers.Serializer] = None,
    description: str = None
) -> Dict[Union[int, str], Any]:
    """
    Get response schema for a status code.
    
    Args:
        status_code: HTTP status code (int or string like "200-all")
        serializer: Optional serializer for the response
        description: Optional description for the response
        
    Returns:
        Dictionary mapping status code to response schema
    """
    if isinstance(status_code, str):
        code = int(status_code.split('-')[0])
    else:
        code = status_code
    
    if serializer:
        return {
            status_code: OpenApiResponse(
                response=serializer,
                description=description or f"Status {code}"
            )
        }
    
    error_serializer = _get_default_error_serializer(code)
    if error_serializer:
        return {
            status_code: OpenApiResponse(
                response=error_serializer,
                description=description or _get_default_error_description(code)
            )
        }
    
    return {
        status_code: OpenApiResponse(description=description or f"Status {code}")
    }


def _get_default_error_serializer(status_code: int) -> Type[serializers.Serializer]:
    """
    Get default error serializer for a status code.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Error serializer class or None
    """
    mapping = {
        status.HTTP_400_BAD_REQUEST: BadRequestErrorSerializer,
        status.HTTP_401_UNAUTHORIZED: UnauthorizedErrorSerializer,
        status.HTTP_403_FORBIDDEN: ForbiddenErrorSerializer,
        status.HTTP_404_NOT_FOUND: NotFoundErrorSerializer,
        status.HTTP_500_INTERNAL_SERVER_ERROR: InternalServerErrorSerializer,
        status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailableErrorSerializer,
    }
    return mapping.get(status_code)


def _get_default_error_description(status_code: int) -> str:
    """
    Get default error description for a status code.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Error description
    """
    descriptions = {
        status.HTTP_400_BAD_REQUEST: "Bad Request - Invalid input data",
        status.HTTP_401_UNAUTHORIZED: "Unauthorized - Authentication required",
        status.HTTP_403_FORBIDDEN: "Forbidden - Insufficient permissions",
        status.HTTP_404_NOT_FOUND: "Not Found - Resource not found",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
        status.HTTP_503_SERVICE_UNAVAILABLE: "Service Unavailable",
    }
    return descriptions.get(status_code, f"Status {status_code}")


def map_status_codes_to_responses(
    status_codes: list,
    response_serializer: Type[serializers.Serializer] = None,
    custom_mappings: Dict[Union[int, str], Type[serializers.Serializer]] = None
) -> Dict[Union[int, str], Any]:
    """
    Map a list of status codes to response schemas.
    
    Args:
        status_codes: List of status codes (int or string)
        response_serializer: Default serializer for success responses (200, 201)
        custom_mappings: Custom mappings for specific status codes
        
    Returns:
        Dictionary mapping status codes to response schemas
    """
    responses = {}
    custom_mappings = custom_mappings or {}
    
    for status_code in status_codes:
        if status_code in custom_mappings:
            serializer = custom_mappings[status_code]
            responses.update(get_status_code_response(status_code, serializer))
        elif status_code in [ResponseStatusCodes.OK, ResponseStatusCodes.OK_ALL, ResponseStatusCodes.OK_PAGINATED]:
            if response_serializer:
                if status_code == ResponseStatusCodes.OK_PAGINATED:
                    responses[status_code] = OpenApiResponse(
                        response=response_serializer(many=True),
                        description="Paginated list response"
                    )
                elif status_code == ResponseStatusCodes.OK_ALL:
                    responses[status_code] = OpenApiResponse(
                        response=response_serializer(many=True),
                        description="Unpaginated list response"
                    )
                else:
                    responses[status_code] = response_serializer
        elif status_code == ResponseStatusCodes.CREATED:
            if response_serializer:
                responses[status_code] = response_serializer
            else:
                responses.update(get_status_code_response(status_code))
        else:
            responses.update(get_status_code_response(status_code))
    
    return responses


def get_payment_status_codes() -> list:
    """
    Get standard status codes for payment endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.CREATED,
        ResponseStatusCodes.BAD_REQUEST,
        ResponseStatusCodes.NOT_FOUND,
        ResponseStatusCodes.SERVER_ERROR,
        ResponseStatusCodes.SERVICE_UNAVAILABLE,
    ]


def get_payment_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for payment endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.NOT_FOUND: TransactionNotFoundErrorSerializer,
        ResponseStatusCodes.SERVER_ERROR: PaymentFailedErrorSerializer,
        ResponseStatusCodes.SERVICE_UNAVAILABLE: PaymentGatewayErrorSerializer,
        ResponseStatusCodes.BAD_REQUEST: BadRequestErrorSerializer,
    }


def get_order_status_codes() -> list:
    """
    Get standard status codes for order endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.CREATED,
        ResponseStatusCodes.BAD_REQUEST,
        ResponseStatusCodes.NOT_FOUND,
        ResponseStatusCodes.SERVER_ERROR,
    ]


def get_order_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for order endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.NOT_FOUND: OrderNotFoundErrorSerializer,
        ResponseStatusCodes.BAD_REQUEST: EmptyCartErrorSerializer,
        ResponseStatusCodes.SERVER_ERROR: InsufficientStockErrorSerializer,
    }


def get_product_status_codes() -> list:
    """
    Get standard status codes for product endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.OK,
        ResponseStatusCodes.BAD_REQUEST,
        ResponseStatusCodes.NOT_FOUND,
    ]


def get_product_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for product endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.NOT_FOUND: ProductNotFoundErrorSerializer,
        ResponseStatusCodes.BAD_REQUEST: ValidationErrorSerializer,
    }


def get_category_status_codes() -> list:
    """
    Get standard status codes for category endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.OK,
        ResponseStatusCodes.BAD_REQUEST,
        ResponseStatusCodes.NOT_FOUND,
    ]


def get_category_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for category endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.NOT_FOUND: CategoryNotFoundErrorSerializer,
        ResponseStatusCodes.BAD_REQUEST: BadRequestErrorSerializer,
    }


def get_cart_status_codes() -> list:
    """
    Get standard status codes for cart endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.OK,
        ResponseStatusCodes.CREATED,
        ResponseStatusCodes.BAD_REQUEST,
        ResponseStatusCodes.NOT_FOUND,
    ]


def get_cart_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for cart endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.NOT_FOUND: CartItemNotFoundErrorSerializer,
        ResponseStatusCodes.BAD_REQUEST: InsufficientStockErrorSerializer,
    }


def get_admin_status_codes() -> list:
    """
    Get standard status codes for admin endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.OK,
        ResponseStatusCodes.CREATED,
        ResponseStatusCodes.BAD_REQUEST,
        ResponseStatusCodes.UNAUTHORIZED,
        ResponseStatusCodes.FORBIDDEN,
        ResponseStatusCodes.NOT_FOUND,
    ]


def get_admin_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for admin endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.UNAUTHORIZED: UnauthorizedAccessErrorSerializer,
        ResponseStatusCodes.FORBIDDEN: ForbiddenAccessErrorSerializer,
        ResponseStatusCodes.BAD_REQUEST: ValidationErrorSerializer,
        ResponseStatusCodes.NOT_FOUND: NotFoundErrorSerializer,
    }


def get_invoice_status_codes() -> list:
    """
    Get standard status codes for invoice endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.OK,
        ResponseStatusCodes.CREATED,
        ResponseStatusCodes.BAD_REQUEST,
        ResponseStatusCodes.NOT_FOUND,
    ]


def get_invoice_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for invoice endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.NOT_FOUND: InvoiceNotFoundErrorSerializer,
        ResponseStatusCodes.BAD_REQUEST: BadRequestErrorSerializer,
    }


def get_transaction_status_codes() -> list:
    """
    Get standard status codes for transaction endpoints.
    
    Returns:
        List of status codes
    """
    return [
        ResponseStatusCodes.OK,
        ResponseStatusCodes.OK_PAGINATED,
        ResponseStatusCodes.NOT_FOUND,
    ]


def get_transaction_status_code_mappings() -> Dict[Union[int, str], Type[serializers.Serializer]]:
    """
    Get custom status code mappings for transaction endpoints.
    
    Returns:
        Dictionary mapping status codes to error serializers
    """
    return {
        ResponseStatusCodes.NOT_FOUND: TransactionNotFoundErrorSerializer,
    }

