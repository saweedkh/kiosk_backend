from rest_framework.views import exception_handler
from apps.core.exceptions import BaseAPIException


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        if isinstance(exc, BaseAPIException):
            custom_response_data = {
                'error': exc.default_detail,
                'detail': str(exc.detail) if exc.detail else exc.default_detail,
                'code': exc.default_code
            }
            response.data = custom_response_data
        else:
            custom_response_data = {
                'error': 'An error occurred',
                'detail': str(exc) if exc else 'Unknown error',
                'code': 'error'
            }
            response.data = custom_response_data
    
    return response

