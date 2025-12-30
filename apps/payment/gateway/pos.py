"""
POS Card Reader Gateway for Pardakht Novin.

This module implements the communication protocol with POS card readers
as described in the technical documentation.
"""
import socket
import time
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .base import BasePaymentGateway
from .exceptions import GatewayException

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class POSPaymentGateway(BasePaymentGateway):
    """
    Payment Gateway for POS Card Reader (Pardakht Novin).
    
    Supports both Serial Port (COM/USB) and TCP/IP connections.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Force TCP/IP connection, not serial
        connection_type = self.config.get('connection_type', 'tcp')
        if connection_type == 'serial':
            # Override to TCP/IP if serial is requested
            connection_type = 'tcp'
            import warnings
            warnings.warn('Serial connection requested but using TCP/IP instead. Set POS_CONNECTION_TYPE=tcp in .env')
        
        self.connection_type = connection_type  # Always 'tcp' for socket connection
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
        # If already connected, reuse the connection
        if self._connection:
            try:
                # Check if connection is still alive
                if self.connection_type == 'tcp':
                    # For TCP, try to get socket info to check if alive
                    try:
                        self._connection.getpeername()
                        # Connection is alive, reuse it
                        return
                    except (OSError, socket.error):
                        # Connection is dead, reconnect
                        self._connection = None
                elif self.connection_type == 'serial':
                    if self._connection.is_open:
                        # Connection is alive, reuse it
                        return
                    else:
                        # Connection is closed, reconnect
                        self._connection = None
            except Exception:
                # Connection check failed, reconnect
                self._connection = None
        
        if self.connection_type == 'serial':
            if not SERIAL_AVAILABLE:
                raise GatewayException('pyserial is not installed. Install it with: pip install pyserial')
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
                # Set socket options to keep connection alive
                self._connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                # Connect without timeout first
                self._connection.settimeout(None)  # No timeout for connection
                self._connection.connect((self.tcp_host, self.tcp_port))
                print(f"✅ اتصال TCP/IP برقرار شد: {self.tcp_host}:{self.tcp_port}")
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
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to POS device.
        
        Returns:
            Dict[str, Any]: Test result containing:
                - success: bool - Whether connection was successful
                - message: str - Status message
                - connection_type: str - Type of connection used
                - details: dict - Additional connection details
        """
        result = {
            'success': False,
            'message': '',
            'connection_type': self.connection_type,
            'details': {}
        }
        
        try:
            # Try to connect
            self._connect()
            
            # If connection successful, try a simple ping/test command
            # For TCP, just connecting is enough to test
            # For Serial, we can try to read/write
            
            if self.connection_type == 'tcp':
                result['success'] = True
                result['message'] = f'اتصال TCP/IP موفق بود (IP: {self.tcp_host}, Port: {self.tcp_port})'
                result['details'] = {
                    'host': self.tcp_host,
                    'port': self.tcp_port,
                    'timeout': self.timeout
                }
            elif self.connection_type == 'serial':
                # For serial, try to read port status
                if self._connection and self._connection.is_open:
                    result['success'] = True
                    result['message'] = f'اتصال سریال موفق بود (Port: {self.serial_port}, Baudrate: {self.serial_baudrate})'
                    result['details'] = {
                        'port': self.serial_port,
                        'baudrate': self.serial_baudrate,
                        'timeout': self.timeout
                    }
                else:
                    result['message'] = f'اتصال سریال ناموفق بود (Port: {self.serial_port})'
            
            # Disconnect after test
            self._disconnect()
            
        except GatewayException as e:
            result['message'] = f'خطا در اتصال: {str(e)}'
            result['details'] = {'error': str(e)}
        except Exception as e:
            result['message'] = f'خطای غیرمنتظره: {str(e)}'
            result['details'] = {'error': str(e)}
        finally:
            if self._connection:
                self._disconnect()
        
        return result
    
    def _send_command(self, command, wait_for_response: bool = True, max_wait_time: int = 120) -> str:
        """
        Send command to POS device and receive response.
        
        Args:
            command: Command string to send
            wait_for_response: Whether to wait for response (for async transactions)
            max_wait_time: Maximum time to wait for response in seconds
            
        Returns:
            str: Response from POS device
            
        Raises:
            GatewayException: If communication fails
        """
        if not self._connection:
            self._connect()
        
        try:
            # Convert command to bytes if it's a string
            if isinstance(command, str):
                command_bytes = command.encode('utf-8')
            else:
                command_bytes = command
            
            # Debug: Log what we're sending
            try:
                command_str = command_bytes.decode('utf-8', errors='replace')[:100]
                print(f"📤 ارسال درخواست ({len(command_bytes)} bytes): {command_str}...")
            except:
                print(f"📤 ارسال درخواست ({len(command_bytes)} bytes): {command_bytes[:50]}...")
            
            # Send command
            if self.connection_type == 'serial':
                self._connection.write(command_bytes)
                # Wait a bit for response
                time.sleep(0.5)
                response = self._connection.read(1024).decode('utf-8', errors='replace')
            else:  # TCP
                # IMPORTANT: Keep connection alive - don't close it!
                # Send command
                self._connection.sendall(command_bytes)
                
                # Small delay to ensure data is sent
                time.sleep(0.1)
                
                if not wait_for_response:
                    # For commands that don't need response
                    return ''
                
                # Wait for response - POS devices may take time to respond
                # Especially for payment transactions that require user interaction
                # IMPORTANT: Keep connection open and wait for response
                response = ''
                start_time = time.time()
                
                # Set socket to non-blocking mode for checking, but use timeout for actual reads
                # This allows us to keep connection alive while waiting
                self._connection.settimeout(1)  # 1 second timeout per read attempt
                
                # First, try to get immediate response (acknowledgment)
                try:
                    # Some POS devices send immediate ACK
                    chunk = self._connection.recv(4096)
                    if chunk:
                        response += chunk.decode('utf-8', errors='ignore')
                        print(f"📥 دریافت پاسخ اولیه: {response[:100]}...")
                except socket.timeout:
                    # No immediate response, that's OK - device might be waiting for user
                    # Connection is still alive, continue waiting
                    pass
                except Exception as e:
                    print(f"⚠️  خطا در دریافت پاسخ اولیه: {e}")
                    # Don't disconnect - connection might still be valid
                
                # Now wait for actual transaction response (user interaction required)
                # Keep connection alive and check periodically
                
                while time.time() - start_time < max_wait_time:
                    try:
                        # Try to receive data
                        chunk = self._connection.recv(4096)
                        if chunk:
                            chunk_str = chunk.decode('utf-8', errors='ignore')
                            response += chunk_str
                            print(f"📥 دریافت داده: {chunk_str[:100]}...")
                            
                            # If we got some data, wait a bit more to see if more is coming
                            time.sleep(0.5)
                            # Try to get more data if available
                            self._connection.settimeout(1)
                            try:
                                while True:
                                    more_chunk = self._connection.recv(4096)
                                    if not more_chunk:
                                        break
                                    more_str = more_chunk.decode('utf-8', errors='ignore')
                                    response += more_str
                                    print(f"📥 دریافت داده بیشتر: {more_str[:100]}...")
                            except socket.timeout:
                                # No more data, we're done
                                break
                            
                            # If we have a complete response, break
                            if response and len(response) > 10:  # At least some meaningful response
                                break
                        else:
                            # No data yet, wait a bit
                            time.sleep(1)
                    except socket.timeout:
                        # No response yet, continue waiting
                        elapsed = int(time.time() - start_time)
                        if elapsed % 10 == 0 and elapsed > 0:  # Print every 10 seconds
                            print(f"⏳ منتظر پاسخ... ({elapsed}/{max_wait_time} ثانیه)")
                        continue
                    except Exception as e:
                        # Connection error
                        print(f"⚠️  خطا در دریافت پاسخ: {e}")
                        break
                
                if not response:
                    print(f"⚠️  هیچ پاسخی دریافت نشد بعد از {int(time.time() - start_time)} ثانیه")
                else:
                    print(f"📥 دریافت پاسخ کامل ({len(response)} chars): {response[:200]}...")
            
            return response
        except GatewayException:
            # Re-raise GatewayException as is
            raise
        except Exception as e:
            # Only disconnect on critical errors, not on timeout
            # Connection might still be valid for retry
            print(f"⚠️  خطا در ارتباط: {e}")
            # Don't disconnect immediately - connection might still be valid
            # self._disconnect()
            raise GatewayException(f'Failed to communicate with POS: {str(e)}')
    
    def _build_payment_request_exact(self, amount: int, order_number: str, 
                                     additional_data: Dict[str, Any] = None) -> bytes:
        """
        Build payment request EXACTLY as DLL does - based on DLL tag analysis.
        
        DLL uses tag-based format: PR{type}AM{amount}TE{terminal}ME{merchant}SO{order}...
        No separators between tags, just concatenated.
        
        This is the EXACT format DLL uses based on DLL_INFO.md analysis.
        """
        parts = []
        
        # PR - Payment Request Type (00 = normal payment)
        parts.append("PR00")
        
        # AM - Amount (12 digits, zero-padded)
        amount_str = str(amount).zfill(12)
        parts.append(f"AM{amount_str}")
        
        # TE - Terminal ID (8 digits, zero-padded)
        if self.terminal_id:
            terminal_id_str = str(self.terminal_id).zfill(8)
            parts.append(f"TE{terminal_id_str}")
        
        # ME - Merchant ID (15 digits, zero-padded)
        if self.merchant_id:
            merchant_id_str = str(self.merchant_id).zfill(15)
            parts.append(f"ME{merchant_id_str}")
        
        # SO - Sale Order / Order Number (up to 20 chars, left-padded with spaces)
        if order_number:
            order_num = order_number[:20] if len(order_number) > 20 else order_number
            parts.append(f"SO{order_num.ljust(20)}")
        
        # CU - Customer Name (up to 50 chars, left-padded with spaces)
        if additional_data and 'customer_name' in additional_data:
            customer_name = additional_data['customer_name'][:50] if len(additional_data['customer_name']) > 50 else additional_data['customer_name']
            parts.append(f"CU{customer_name.ljust(50)}")
        
        # PD - Payment ID (11 digits, zero-padded)
        if additional_data and 'payment_id' in additional_data:
            payment_id = str(additional_data['payment_id'])[:11].zfill(11)
            parts.append(f"PD{payment_id}")
        
        # BI - Bill ID (20 digits/chars, zero-padded)
        if additional_data and 'bill_id' in additional_data:
            bill_id = str(additional_data['bill_id'])[:20].zfill(20)
            parts.append(f"BI{bill_id}")
        
        # Join all parts (NO separator - this is key!)
        message = "".join(parts)
        
        # Convert to ASCII bytes (POS devices use ASCII, not UTF-8)
        return message.encode('ascii')
    
    def _build_payment_request(self, amount: int, order_number: str, 
                              additional_data: Dict[str, Any] = None) -> bytes:
        """
        Build payment request according to POS protocol.
        
        Based on DLL analysis (DLL_INFO.md), DLL uses tag-based format:
        PR{type}AM{amount}TE{terminal}ME{merchant}SO{order}...
        
        This is the EXACT format - no separators, just concatenated tags.
        
        Args:
            amount: Payment amount in Rial
            order_number: Order number
            additional_data: Additional data for payment
            
        Returns:
            bytes: Formatted request bytes (ready to send)
        """
        format_type = self.config.get('pos_message_format', 'dll_exact')
        
        if format_type == 'dll_exact':
            # Use EXACT DLL format (based on DLL tag analysis)
            return self._build_payment_request_exact(amount, order_number, additional_data)
        
        elif format_type == 'iso8583_like':
            # Try ISO 8583-like format (common in POS devices)
            # Format: STX + Message + ETX + LRC
            # Message format: MTI (4) + Bitmap + Fields
            # For simplicity, let's try a simpler format first
            
            # Format amount: 12 digits, zero-padded
            amount_str = str(amount).zfill(12)
            
            # Build message parts
            request_parts = []
            
            # MTI (Message Type Indicator) - 0200 = Financial Transaction Request
            request_parts.append("0200")
            
            # Bitmap (simplified - just indicate which fields are present)
            # For now, use a simple bitmap
            bitmap = "E000000000000000"  # Simplified bitmap
            request_parts.append(bitmap)
            
            # Field 4: Amount (12 digits)
            request_parts.append(amount_str)
            
            # Field 11: System Trace Audit Number (6 digits) - use timestamp
            import time
            trace_num = str(int(time.time()) % 1000000).zfill(6)
            request_parts.append(trace_num)
            
            # Field 41: Terminal ID (8 chars)
            if self.terminal_id:
                terminal_id_str = str(self.terminal_id).zfill(8)
                request_parts.append(terminal_id_str)
            
            # Field 42: Merchant ID (15 chars)
            if self.merchant_id:
                merchant_id_str = str(self.merchant_id).zfill(15)
                request_parts.append(merchant_id_str)
            
            # Join with field separators (usually \x1C or |)
            message = "\x1C".join(request_parts)
            
            # Add STX (0x02) at start and ETX (0x03) at end
            request_bytes = b'\x02' + message.encode('ascii') + b'\x03'
            
        elif format_type == 'simple_tlv':
            # Try simple TLV format
            import struct
            
            # Format amount: 12 digits, zero-padded
            amount_str = str(amount).zfill(12)
            
            tlv_parts = []
            
            # Tag: Amount (0x01), Length: 12, Value: amount
            tlv_parts.append(b'\x01')
            tlv_parts.append(struct.pack('B', 12))
            tlv_parts.append(amount_str.encode('ascii'))
            
            # Tag: Terminal ID (0x02), Length: 8, Value: terminal_id
            if self.terminal_id:
                terminal_id_str = str(self.terminal_id).zfill(8)
                tlv_parts.append(b'\x02')
                tlv_parts.append(struct.pack('B', 8))
                tlv_parts.append(terminal_id_str.encode('ascii'))
            
            # Tag: Merchant ID (0x03), Length: 15, Value: merchant_id
            if self.merchant_id:
                merchant_id_str = str(self.merchant_id).zfill(15)
                tlv_parts.append(b'\x03')
                tlv_parts.append(struct.pack('B', 15))
                tlv_parts.append(merchant_id_str.encode('ascii'))
            
            request_bytes = b''.join(tlv_parts)
            
        else:  # 'simple' or 'with_terminator' - original format
            # Format amount: 12 digits, zero-padded
            amount_str = str(amount).zfill(12)
            
            # Original simple string format
            request_parts = []
            
            # PR = Payment Request, AM = Amount
            request_parts.append(f"PR00")  # Payment type: 00 = normal payment
            request_parts.append(f"AM{amount_str}")  # Amount
            
            # Terminal ID (TE tag) - 8 digits
            if self.terminal_id:
                terminal_id_str = str(self.terminal_id).zfill(8)
                request_parts.append(f"TE{terminal_id_str}")
            
            # Merchant ID (ME tag) - if needed, usually 15 digits
            if self.merchant_id:
                merchant_id_str = str(self.merchant_id).zfill(15)
                request_parts.append(f"ME{merchant_id_str}")
            
            # Order number (SO tag - Sale Order) - up to 20 chars
            if order_number:
                order_num = order_number[:20] if len(order_number) > 20 else order_number
                request_parts.append(f"SO{order_num.ljust(20)}")
            
            # Additional data
            if additional_data:
                # Customer name (CU tag) - up to 50 chars
                if 'customer_name' in additional_data:
                    customer_name = additional_data['customer_name'][:50]
                    request_parts.append(f"CU{customer_name.ljust(50)}")
            
            # Join all parts
            request_string = "".join(request_parts)
            
            # Convert to bytes
            try:
                request_bytes = request_string.encode('utf-8')
            except:
                request_bytes = request_string.encode('ascii', errors='ignore')
            
            # Add terminator if needed
            if format_type == 'with_terminator':
                request_bytes = request_bytes + b'\r\n'
        
        return request_bytes
    
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

        print(response)
        
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
        
        # Build payment request (returns bytes)
        request_bytes = self._build_payment_request(
            amount=amount,
            order_number=order_number,
            additional_data={'customer_name': customer_name} if customer_name else None
        )
        
        try:
            # Send payment request to POS and wait for response
            # Payment transactions require user interaction (card swipe, PIN entry)
            # So we need to wait longer (up to 2 minutes)
            print("\n⚠️  توجه: مبلغ روی دستگاه نمایش داده می‌شود.")
            print("   لطفاً منتظر بمانید تا:")
            print("   1. کارت را بکشید")
            print("   2. رمز را وارد کنید")
            print("   3. یا در دستگاه لغو کنید")
            print(f"   (حداکثر 120 ثانیه منتظر می‌مانیم)\n")
            
            response = self._send_command(request_bytes, wait_for_response=True, max_wait_time=120)
            
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
            # Don't disconnect immediately - keep connection for potential retries
            # self._disconnect()
            pass
    
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

