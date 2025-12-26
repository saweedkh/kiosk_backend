from django.conf import settings
from typing import Dict, Any
from .base import BasePaymentGateway
from .mock import MockPaymentGateway
from .exceptions import GatewayException


class PaymentGatewayAdapter:
    
    @staticmethod
    def get_gateway() -> BasePaymentGateway:
        config = settings.PAYMENT_GATEWAY_CONFIG
        gateway_name = config.get('gateway_name', 'mock')
        
        if gateway_name == 'mock':
            return MockPaymentGateway(config)
        
        raise GatewayException(f'Unknown gateway: {gateway_name}')
    
    @staticmethod
    def is_gateway_active() -> bool:
        config = settings.PAYMENT_GATEWAY_CONFIG
        return config.get('is_active', False)

