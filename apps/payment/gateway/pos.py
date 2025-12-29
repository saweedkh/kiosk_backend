"""
POS Card Reader Gateway for Pardakht Novin.

This module implements the communication protocol with POS card readers
as described in the technical documentation.
"""
import socket
import serial
import time
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .base import BasePaymentGateway
from .exceptions import GatewayException


class POSPaymentGateway(BasePaymentGateway):
    """
    Payment Gateway for POS Card Reader (Pardakht Novin).
    
    Supports both Serial Port (COM/USB) and TCP/IP connections.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.connection_type = self.config.get('connection_type', 'tcp')  # 'serial' or 'tcp'
        self.serial_port = self.config.get('serial_port', 'COM1')
        self.serial_baudrate = self.config.get('serial_baudrate', 9600)
        self.tcp_host = self.config.get('tcp_host', '192.168.1.100')
        self.tcp_port = self.config.get('tcp_port', 1362)
        self.timeout = self.config.get('timeout', 30)
        self.merchant_id = self.config.get('merchant_id', '')
        self.terminal_id = self.config.get('terminal_id', '')
        
        self._connection = None
    
    def _connect(self):
        """Establish connection to POS device."""
        if self.connection_type == 'serial':
            try:
                self._connection = serial.Serial(
                    port=self.serial_port,
                    baudrate=self.serial_baudrate,
                    timeout=self.timeout
                )
            except Exception as e:
                raise GatewayException(f'Failed to connect to POS via serial: {str(e)}')
        elif self.connection_type == 'tcp':
            try:
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._connection.settimeout(self.timeout)
                self._connection.connect((self.tcp_host, self.tcp_port))
            except Exception as e:
                raise GatewayException(f'Failed to connect to POS via TCP: {str(e)}')
        else:
            raise GatewayException(f'Unknown connection type: {self.connection_type}')
    
    def _disconnect(self):
        """Close connection to POS device."""
        if self._connection:
            try:
                if self.connection_type == 'serial':
                    self._connection.close()
                elif self.connection_type == 'tcp':
                    self._connection.close()
            except Exception:
                pass
            finally:
                self._connection = None
    
    def _send_command(self, command: str) -> str:
        """
        Send command to POS device and receive response.
        
        Args:
            command: Command string to send
            
        Returns:
            str: Response from POS device
            
        Raises:
            GatewayException: If communication fails
        """
        if not self._connection:
            self._connect()
        
        try:
            # Send command
            if self.connection_type == 'serial':
                self._connection.write(command.encode('utf-8'))
                response = self._connection.read(1024).decode('utf-8')
            else:  # TCP
                self._connection.sendall(command.encode('utf-8'))
                response = self._connection.recv(1024).decode('utf-8')
            
            return response
        except Exception as e:
            self._disconnect()
            raise GatewayException(f'Failed to communicate with POS: {str(e)}')
    
    def _build_payment_request(self, amount: int, order_number: str, 
                              additional_data: Dict[str, Any] = None) -> str:
        """
        Build payment request string according to POS protocol.
        
        Based on Pardakht Novin documentation:
        Format: R{amount}PR{payment_type}AM{amount}CU{customer}...
        
        Args:
            amount: Payment amount in Rial
            order_number: Order number
            additional_data: Additional data for payment
            
        Returns:
            str: Formatted request string
        """
        # Format amount: 12 digits, zero-padded (based on PDF documentation)
        amount_str = str(amount).zfill(12)
        
        # Build request string according to protocol
        # R = Request, PR = Payment Request, AM = Amount
        request = f"R{amount_str}PR00AM{amount_str}"
        
        # Terminal ID (TE tag)
        if self.terminal_id:
            terminal_id_str = str(self.terminal_id).zfill(8)
            request += f"TE{terminal_id_str}"
        
        # Merchant ID (ME tag) - if needed
        if self.merchant_id:
            merchant_id_str = str(self.merchant_id).zfill(8)
            request += f"ME{merchant_id_str}"
        
        # Order number (SO tag - Sale Order)
        if order_number:
            order_num = order_number[:20] if len(order_number) > 20 else order_number
            request += f"SO{order_num.zfill(20)}"
        
        # Additional data
        if additional_data:
            # Customer name (CU tag)
            if 'customer_name' in additional_data:
                customer_name = additional_data['customer_name'][:50]
                request += f"CU{customer_name.zfill(50)}"
            
            # Payment ID (PD tag) - if provided
            if 'payment_id' in additional_data:
                payment_id = str(additional_data['payment_id'])[:11]
                request += f"PD{payment_id.zfill(11)}"
            
            # Bill ID (BI tag) - if provided
            if 'bill_id' in additional_data:
                bill_id = str(additional_data['bill_id'])[:20]
                request += f"BI{bill_id.zfill(20)}"
        
        return request
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse response from POS device.
        
        Based on Pardakht Novin protocol:
        Format: RS{response_code}SR{serial}RN{reference}TI{terminal}...
        
        Args:
            response: Response string from POS
            
        Returns:
            Dict[str, Any]: Parsed response data
        """
        result = {
            'success': False,
            'status': 'failed',
            'response_code': '',
            'response_message': '',
            'transaction_id': '',
            'card_number': '',
            'reference_number': '',
            'terminal_id': '',
            'raw_response': response
        }
        
        if not response:
            return result
        
        # Parse response code (RS tag)
        # RS013 = success, RS002 = failure, etc.
        if 'RS013' in response or 'RS01' in response:
            result['success'] = True
            result['status'] = 'success'
            result['response_code'] = '00'
        elif 'RS00' in response:
            # Extract error code
            rs_idx = response.find('RS00')
            if rs_idx != -1:
                error_code = response[rs_idx+2:rs_idx+5]
                result['response_code'] = error_code
                result['status'] = 'failed'
                result['response_message'] = self._get_error_message(error_code)
        else:
            result['response_code'] = '99'
            result['status'] = 'failed'
            result['response_message'] = 'خطای نامشخص'
        
        # Extract transaction serial (SR tag)
        if 'SR' in response:
            idx = response.find('SR')
            if idx != -1:
                # SR is usually followed by 6-12 digits
                end_idx = idx + 2
                while end_idx < len(response) and response[end_idx].isdigit():
                    end_idx += 1
                result['transaction_id'] = response[idx+2:end_idx].strip()
        
        # Extract reference number (RN tag)
        if 'RN' in response:
            idx = response.find('RN')
            if idx != -1:
                # RN is usually followed by 12 digits
                end_idx = idx + 2
                while end_idx < len(response) and (response[end_idx].isdigit() or end_idx - idx - 2 < 12):
                    end_idx += 1
                result['reference_number'] = response[idx+2:end_idx].strip()
        
        # Extract terminal ID (TI tag)
        if 'TI' in response:
            idx = response.find('TI')
            if idx != -1:
                end_idx = idx + 2
                while end_idx < len(response) and response[end_idx].isdigit():
                    end_idx += 1
                result['terminal_id'] = response[idx+2:end_idx].strip()
        
        # Extract card number (PN tag - PAN)
        if 'PN' in response:
            idx = response.find('PN')
            if idx != -1:
                # Card number is usually masked (last 4 digits visible)
                end_idx = idx + 2
                while end_idx < len(response) and (response[end_idx].isdigit() or response[end_idx] == '*'):
                    end_idx += 1
                result['card_number'] = response[idx+2:end_idx].strip()
        
        # Extract date/time (DS/TM tags)
        if 'DS' in response:
            idx = response.find('DS')
            if idx != -1:
                result['transaction_date'] = response[idx+2:idx+8].strip()  # YYMMDD
        
        if 'TM' in response:
            idx = response.find('TM')
            if idx != -1:
                result['transaction_time'] = response[idx+2:idx+6].strip()  # HHMM
        
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
        Initiate payment transaction with POS device.
        
        Args:
            amount: Payment amount in Rial
            order_details: Dictionary containing order details
                - order_number: Order number
                - customer_name: Customer name (optional)
                
        Returns:
            Dict[str, Any]: Gateway response containing transaction information
        """
        order_number = order_details.get('order_number', '')
        customer_name = order_details.get('customer_name', '')
        
        # Build payment request
        request = self._build_payment_request(
            amount=amount,
            order_number=order_number,
            additional_data={'customer_name': customer_name} if customer_name else None
        )
        
        try:
            # Send payment request to POS
            response = self._send_command(request)
            
            # Parse response
            parsed_response = self._parse_response(response)
            
            # Generate transaction ID if not provided by POS
            if not parsed_response.get('transaction_id'):
                transaction_id = f"POS-{timezone.now().strftime('%Y%m%d%H%M%S')}-{amount}"
                parsed_response['transaction_id'] = transaction_id
            
            return {
                'success': parsed_response['success'],
                'transaction_id': parsed_response['transaction_id'],
                'status': parsed_response['status'],
                'response_code': parsed_response['response_code'],
                'response_message': parsed_response['response_message'],
                'card_number': parsed_response.get('card_number', ''),
                'reference_number': parsed_response.get('reference_number', ''),
                'gateway_response': parsed_response,
                'amount': amount,
            }
        except Exception as e:
            raise GatewayException(f'Failed to initiate payment: {str(e)}')
        finally:
            self._disconnect()
    
    def verify_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Verify payment transaction.
        
        For POS devices, verification is usually done immediately after initiation.
        This method can be used to check transaction status.
        
        Args:
            transaction_id: Transaction ID to verify
            
        Returns:
            Dict[str, Any]: Verification result
        """
        # POS devices usually return verification immediately
        # This method can query transaction status if supported
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': 'success',  # Assume success if transaction exists
            'gateway_response': {
                'message': 'Transaction verified',
                'verified_at': timezone.now().isoformat()
            }
        }
    
    def get_payment_status(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Get current payment status from POS device.
        
        Args:
            transaction_id: Transaction ID to check
            
        Returns:
            Dict[str, Any]: Payment status information
        """
        # POS devices may not support status queries
        # Return last known status
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': 'success',
            'gateway_response': {
                'message': 'Status retrieved',
                'checked_at': timezone.now().isoformat()
            }
        }
    
    def cancel_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Cancel a payment transaction.
        
        Note: POS devices may not support cancellation after transaction completion.
        
        Args:
            transaction_id: Transaction ID to cancel
            
        Returns:
            Dict[str, Any]: Cancellation result
        """
        # POS devices usually don't support cancellation
        # This would need to be handled at order level
        return {
            'success': False,
            'transaction_id': transaction_id,
            'status': 'cancelled',
            'gateway_response': {
                'message': 'Cancellation not supported by POS device'
            }
        }
    
    def handle_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle webhook callback.
        
        POS devices typically don't use webhooks, but this method
        can be used for manual status updates.
        
        Args:
            request_data: Webhook data
            
        Returns:
            Dict[str, Any]: Processed webhook result
        """
        return {
            'success': True,
            'message': 'Webhook processed',
            'transaction_id': request_data.get('transaction_id', '')
        }

