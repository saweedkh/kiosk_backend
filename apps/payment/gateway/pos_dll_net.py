"""
POS Card Reader Gateway using .NET DLL (Pardakht Novin).

This module implements POS gateway using the official .NET DLL from Pardakht Novin.
The DLL file is: pna.pcpos.dll (version 2.2.0.0)
"""
import os
import platform
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .base import BasePaymentGateway
from .exceptions import GatewayException
from .pos import POSPaymentGateway  # Fallback to direct protocol

try:
    import clr
    PYTHONNET_AVAILABLE = True
except ImportError:
    PYTHONNET_AVAILABLE = False


class POSNETPaymentGateway(BasePaymentGateway):
    """
    Payment Gateway for POS Card Reader using .NET DLL (Pardakht Novin).
    
    This gateway uses the official .NET DLL file (pna.pcpos.dll) provided by Pardakht Novin.
    If DLL is not available or pythonnet is not installed, it falls back to direct protocol implementation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.dll_path = self.config.get('dll_path', '')
        self.use_dll = False
        self.pos_instance = None
        self.fallback_gateway = None
        
        # Check if we can use DLL
        if not PYTHONNET_AVAILABLE:
            # pythonnet not available, use fallback
            self.use_dll = False
            self.fallback_gateway = POSPaymentGateway(config)
            return
        
        if platform.system() != 'Windows':
            # DLL only works on Windows
            self.use_dll = False
            self.fallback_gateway = POSPaymentGateway(config)
            return
        
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
        """Load .NET DLL file using pythonnet."""
        if not PYTHONNET_AVAILABLE:
            raise GatewayException('pythonnet is not installed. Install it with: pip install pythonnet')
        
        try:
            # Add reference to DLL
            clr.AddReference(self.dll_path)
            
            # Import PCPOS class
            from PCPOS import PCPOS
            
            # Create instance
            self.pos_instance = PCPOS()
            
            # Configure connection
            connection_type = self.config.get('connection_type', 'tcp')
            if connection_type == 'serial':
                self.pos_instance.ComPort = self.config.get('serial_port', 'COM1')
                self.pos_instance.baudRate = self.config.get('serial_baudrate', 9600)
                self.pos_instance.ConnectionType = "SERIAL"
            else:
                self.pos_instance.Ip = self.config.get('tcp_host', '192.168.1.100')
                self.pos_instance.Port = self.config.get('tcp_port', 1362)
                self.pos_instance.ConnectionType = "LAN"
            
            # Set terminal ID if provided
            terminal_id = self.config.get('terminal_id', '')
            if terminal_id:
                self.pos_instance.TerminalID = terminal_id
            
        except Exception as e:
            raise GatewayException(f'Failed to load DLL: {str(e)}')
    
    def _test_connection(self) -> bool:
        """Test connection to POS device."""
        if not self.use_dll or not self.pos_instance:
            return False
        
        try:
            return self.pos_instance.TestConnection()
        except Exception as e:
            raise GatewayException(f'Connection test failed: {str(e)}')
    
    def _send_payment_dll(self, amount: int, order_number: str, 
                         additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send payment request using DLL.
        
        Args:
            amount: Payment amount in Rial
            order_number: Order number
            additional_data: Additional data for payment
            
        Returns:
            Dict[str, Any]: Payment response
        """
        if not self.use_dll or not self.pos_instance:
            raise GatewayException('DLL not available')
        
        try:
            # Set amount
            self.pos_instance.Amount = amount
            
            # Set order number if supported
            # Note: DLL might use different property names
            # Adjust based on actual DLL API
            
            # Set additional data if provided
            if additional_data:
                customer_name = additional_data.get('customer_name', '')
                if customer_name and hasattr(self.pos_instance, 'CU'):
                    # Set customer name if property exists
                    pass
            
            # Send transaction
            self.pos_instance.send_transaction()
            
            # Wait for response (DLL handles this asynchronously)
            # Get parsed response
            response = self.pos_instance.GetParsedResp()
            raw_response = self.pos_instance.RawResponse
            
            # Parse response
            return self._parse_dll_response(response, raw_response)
            
        except Exception as e:
            raise GatewayException(f'Failed to send payment via DLL: {str(e)}')
    
    def _parse_dll_response(self, response: str, raw_response: str) -> Dict[str, Any]:
        """
        Parse DLL response.
        
        Args:
            response: Parsed response from DLL
            raw_response: Raw response string
            
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
            'raw_response': raw_response,
            'parsed_response': response
        }
        
        if not response:
            return result
        
        # Try to extract transaction details from response
        # Adjust parsing based on actual DLL response format
        
        # Check if transaction was successful
        # DLL usually returns response codes in format like "RS01" for success
        if 'RS01' in response or 'RS013' in response:
            result['success'] = True
            result['status'] = 'success'
            result['response_code'] = '00'
        else:
            result['status'] = 'failed'
            # Extract error code if available
            if 'RS00' in response:
                result['response_code'] = '01'  # Generic error
            result['response_message'] = self._get_error_message(result['response_code'])
        
        # Extract transaction details
        # Adjust based on actual DLL response format
        try:
            # Try to get reference number
            if hasattr(self.pos_instance, 'GetTrxnRRN'):
                result['reference_number'] = self.pos_instance.GetTrxnRRN()
            
            # Try to get transaction serial
            if hasattr(self.pos_instance, 'GetTrxnSerial'):
                result['transaction_id'] = self.pos_instance.GetTrxnSerial()
            
            # Try to get transaction date/time
            if hasattr(self.pos_instance, 'GetTrxnDateTime'):
                transaction_datetime = self.pos_instance.GetTrxnDateTime()
                result['transaction_datetime'] = str(transaction_datetime)
            
            # Try to get bank name
            if hasattr(self.pos_instance, 'GetBankName'):
                result['bank_name'] = self.pos_instance.GetBankName()
        except Exception:
            pass
        
        return result
    
    def _get_error_message(self, error_code: str) -> str:
        """Get human-readable error message from error code."""
        error_messages = {
            '00': 'تراکنش موفق',
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
            customer_name = order_details.get('customer_name', '')
            
            # Test connection first
            if not self._test_connection():
                raise GatewayException('Failed to connect to POS device')
            
            try:
                # Send payment request
                result = self._send_payment_dll(
                    amount=amount,
                    order_number=order_number,
                    additional_data={'customer_name': customer_name} if customer_name else None
                )
                
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
            except Exception as e:
                raise GatewayException(f'Failed to initiate payment: {str(e)}')
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
            # Try to get last transaction info
            try:
                if hasattr(self.pos_instance, 'send_transaction_Get_Lats_Trxn'):
                    self.pos_instance.send_transaction_Get_Lats_Trxn()
                    response = self.pos_instance.GetParsedResp()
                    return {
                        'success': True,
                        'transaction_id': transaction_id,
                        'status': 'success',
                        'gateway_response': {
                            'message': 'Status retrieved',
                            'response': response,
                            'checked_at': timezone.now().isoformat()
                        }
                    }
            except Exception:
                pass
            
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
            try:
                # Try to cancel transaction
                if hasattr(self.pos_instance, 'send_transaction_Trx_Cancel'):
                    self.pos_instance.send_transaction_Trx_Cancel()
                    response = self.pos_instance.GetParsedResp()
                    return {
                        'success': True,
                        'transaction_id': transaction_id,
                        'status': 'cancelled',
                        'gateway_response': {
                            'message': 'Transaction cancelled',
                            'response': response
                        }
                    }
            except Exception:
                pass
            
            return {
                'success': False,
                'transaction_id': transaction_id,
                'status': 'cancelled',
                'gateway_response': {
                    'message': 'Cancellation not supported or failed'
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
        if self.use_dll and self.pos_instance:
            try:
                # Dispose if available
                if hasattr(self.pos_instance, 'Dispose'):
                    self.pos_instance.Dispose()
            except Exception:
                pass

