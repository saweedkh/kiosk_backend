from django.conf import settings
from typing import Dict, Any
from .base import BasePaymentGateway
from .mock import MockPaymentGateway
from .pos import POSPaymentGateway
from .pos_dll_net import POSNETPaymentGateway
from .pos_bridge import POSBridgeGateway
from .exceptions import GatewayException


class PaymentGatewayAdapter:
    
    @staticmethod
    def get_gateway() -> BasePaymentGateway:
        config = settings.PAYMENT_GATEWAY_CONFIG
        gateway_name = config.get('gateway_name', 'mock')
        use_dll = config.get('pos_use_dll', False)
        use_bridge = config.get('pos_use_bridge', False)
        
        if gateway_name == 'mock':
            return MockPaymentGateway(config)
        elif gateway_name == 'pos':
            # Smart gateway selection:
            # 1. If use_bridge=True, use bridge service (connects to Windows service)
            # 2. If use_dll=True and DLL is available, use DLL (Windows/Mono)
            # 3. Otherwise, use direct protocol (pos.py) - works on ALL platforms
            if use_bridge:
                # Use bridge service - connects to Windows service via HTTP
                # This is the recommended approach for cross-platform support
                return POSBridgeGateway(config)
            elif use_dll:
                # Try DLL first, but it will automatically fallback to pos.py if DLL fails
                return POSNETPaymentGateway(config)
            else:
                # Use direct protocol implementation - 100% cross-platform
                # Works on Windows, macOS (ARM64/x86_64), Linux - no DLL needed!
                return POSPaymentGateway(config)
        
        raise GatewayException(f'Unknown gateway: {gateway_name}')
    
    @staticmethod
    def is_gateway_active() -> bool:
        config = settings.PAYMENT_GATEWAY_CONFIG
        return config.get('is_active', False)

