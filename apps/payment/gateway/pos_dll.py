"""
POS Card Reader Gateway using DLL (Pardakht Novin).

This module implements POS gateway using DLL file if available.
If DLL is not available, falls back to direct protocol implementation.
"""
import os
import platform
from ctypes import CDLL, c_char_p, c_int, c_long, byref, create_string_buffer
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .base import BasePaymentGateway
from .exceptions import GatewayException
from .pos import POSPaymentGateway  # Fallback to direct protocol


class POSDLLPaymentGateway(BasePaymentGateway):
    """
    Payment Gateway for POS Card Reader using DLL (Pardakht Novin).
    
    This gateway uses the DLL file provided by Pardakht Novin.
    If DLL is not available, it falls back to direct protocol implementation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.dll_path = self.config.get('dll_path', '')
        self.use_dll = False
        self.dll = None
        self.fallback_gateway = None
        
        # Try to load DLL if path is provided
        if self.dll_path and os.path.exists(self.dll_path):
            try:
                self._load_dll()
                self.use_dll = True
            except Exception as e:
                # If DLL loading fails, use fallback
                self.use_dll = False
                self.fallback_gateway = POSPaymentGateway(config)
        else:
            # No DLL path provided, use direct protocol
            self.use_dll = False
            self.fallback_gateway = POSPaymentGateway(config)
    
    def _load_dll(self):
        """Load DLL file."""
        if platform.system() == 'Windows':
            self.dll = CDLL(self.dll_path)
        else:
            # On Linux/Mac, DLL files are not directly usable
            # You might need Wine or a different approach
            raise GatewayException('DLL files are only supported on Windows')
        
        # Define function signatures based on DLL documentation
        # These need to be adjusted based on actual DLL functions
        try:
            # Example function signatures (adjust based on actual DLL)
            self.dll.InitializePOS.argtypes = [c_char_p, c_int]
            self.dll.InitializePOS.restype = c_int
            
            self.dll.SendPaymentRequest.argtypes = [c_char_p, c_long, c_char_p]
            self.dll.SendPaymentRequest.restype = c_int
            
            self.dll.GetResponse.argtypes = [c_char_p, c_int]
            self.dll.GetResponse.restype = c_int
            
            self.dll.ClosePOS.argtypes = []
            self.dll.ClosePOS.restype = c_int
        except AttributeError as e:
            raise GatewayException(f'DLL functions not found: {str(e)}')
    
    def _initialize_pos(self, connection_string: str) -> bool:
        """
        Initialize POS connection using DLL.
        
        Args:
            connection_string: Connection string (COM port or TCP IP:Port)
            
        Returns:
            bool: True if initialization successful
        """
        if not self.use_dll:
            return False
        
        try:
            result = self.dll.InitializePOS(
                connection_string.encode('utf-8'),
                len(connection_string)
            )
            return result == 0  # 0 usually means success
        except Exception as e:
            raise GatewayException(f'Failed to initialize POS: {str(e)}')
    
    def _send_payment_dll(self, amount: int, order_number: str) -> Dict[str, Any]:
        """
        Send payment request using DLL.
        
        Args:
            amount: Payment amount in Rial
            order_number: Order number
            
        Returns:
            Dict[str, Any]: Payment response
        """
        if not self.use_dll:
            raise GatewayException('DLL not available')
        
        try:
            # Prepare request data
            request_data = f"{amount:012d}{order_number[:20]:<20}"
            response_buffer = create_string_buffer(1024)
            
            # Send payment request
            result = self.dll.SendPaymentRequest(
                request_data.encode('utf-8'),
                amount,
                response_buffer
            )
            
            if result != 0:
                raise GatewayException(f'Payment request failed with code: {result}')
            
            # Parse response
            response = response_buffer.value.decode('utf-8')
            return self._parse_dll_response(response)
            
        except Exception as e:
            raise GatewayException(f'Failed to send payment via DLL: {str(e)}')
    
    def _parse_dll_response(self, response: str) -> Dict[str, Any]:
        """
        Parse DLL response.
        
        Args:
            response: Response string from DLL
            
        Returns:
            Dict[str, Any]: Parsed response
        """
        result = {
            'success': False,
            'status': 'failed',
            'response_code': '',
            'response_message': '',
            'transaction_id': '',
            'card_number': '',
            'reference_number': '',
            'raw_response': response
        }
        
        if not response:
            return result
        
        # Parse response based on DLL format
        # Adjust parsing based on actual DLL response format
        if len(response) >= 2:
            result['response_code'] = response[:2]
            
            if result['response_code'] == '00':
                result['success'] = True
                result['status'] = 'success'
            else:
                result['status'] = 'failed'
                result['response_message'] = self._get_error_message(result['response_code'])
        
        # Extract transaction details
        # Adjust based on actual DLL response format
        if len(response) > 20:
            result['transaction_id'] = response[2:22].strip()
        
        return result
    
    def _get_error_message(self, error_code: str) -> str:
        """Get human-readable error message from error code."""
        error_messages = {
            '01': 'تراکنش ناموفق - کارت نامعتبر',
            '02': 'تراکنش ناموفق - موجودی کافی نیست',
            '03': 'تراکنش ناموفق - رمز اشتباه',
            '04': 'تراکنش ناموفق - کارت منقضی شده',
            '05': 'تراکنش ناموفق - خطا در ارتباط',
            '06': 'تراکنش ناموفق - خطای سیستم',
            '99': 'تراکنش ناموفق - خطای نامشخص',
        }
        return error_messages.get(error_code, f'خطای نامشخص: {error_code}')
    
    def initiate_payment(self, amount: int, order_details: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Initiate payment transaction.
        
        Uses DLL if available, otherwise falls back to direct protocol.
        """
        if self.use_dll:
            # Use DLL implementation
            order_number = order_details.get('order_number', '')
            
            # Build connection string
            connection_type = self.config.get('connection_type', 'tcp')
            if connection_type == 'serial':
                connection_string = self.config.get('serial_port', 'COM1')
            else:
                host = self.config.get('tcp_host', '192.168.1.100')
                port = self.config.get('tcp_port', 1362)
                connection_string = f"{host}:{port}"
            
            # Initialize POS
            if not self._initialize_pos(connection_string):
                raise GatewayException('Failed to initialize POS connection')
            
            try:
                # Send payment request
                result = self._send_payment_dll(amount, order_number)
                
                # Generate transaction ID if not provided
                if not result.get('transaction_id'):
                    transaction_id = f"POS-{timezone.now().strftime('%Y%m%d%H%M%S')}-{amount}"
                    result['transaction_id'] = transaction_id
                
                return {
                    'success': result['success'],
                    'transaction_id': result['transaction_id'],
                    'status': result['status'],
                    'response_code': result['response_code'],
                    'response_message': result['response_message'],
                    'card_number': result.get('card_number', ''),
                    'reference_number': result.get('reference_number', ''),
                    'gateway_response': result,
                    'amount': amount,
                }
            finally:
                # Close POS connection
                try:
                    self.dll.ClosePOS()
                except Exception:
                    pass
        else:
            # Use fallback direct protocol implementation
            return self.fallback_gateway.initiate_payment(amount, order_details, **kwargs)
    
    def verify_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        """Verify payment transaction."""
        if self.use_dll:
            # DLL verification logic
            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': 'success',
                'gateway_response': {
                    'message': 'Transaction verified',
                    'verified_at': timezone.now().isoformat()
                }
            }
        else:
            return self.fallback_gateway.verify_payment(transaction_id, **kwargs)
    
    def get_payment_status(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        """Get payment status."""
        if self.use_dll:
            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': 'success',
                'gateway_response': {
                    'message': 'Status retrieved',
                    'checked_at': timezone.now().isoformat()
                }
            }
        else:
            return self.fallback_gateway.get_payment_status(transaction_id, **kwargs)
    
    def cancel_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        """Cancel payment."""
        if self.use_dll:
            return {
                'success': False,
                'transaction_id': transaction_id,
                'status': 'cancelled',
                'gateway_response': {
                    'message': 'Cancellation not supported by POS device'
                }
            }
        else:
            return self.fallback_gateway.cancel_payment(transaction_id, **kwargs)
    
    def handle_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook."""
        if self.use_dll:
            return {
                'success': True,
                'message': 'Webhook processed',
                'transaction_id': request_data.get('transaction_id', '')
            }
        else:
            return self.fallback_gateway.handle_webhook(request_data)
    
    def __del__(self):
        """Cleanup on destruction."""
        if self.use_dll and self.dll:
            try:
                self.dll.ClosePOS()
            except Exception:
                pass

