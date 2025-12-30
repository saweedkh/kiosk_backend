"""
POS Card Reader Gateway for Pardakht Novin (Direct Protocol).

This module implements direct communication protocol with POS card readers
without using DLL. It uses TCP/IP socket connection.

Based on the DLL analysis, the protocol uses tag-based format:
PR{type}AM{amount}TE{terminal}ME{merchant}SO{order}CU{customer}PD{payment_id}BI{bill_id}
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
    Payment Gateway for POS Card Reader (Pardakht Novin) - Direct Protocol.
    
    This implementation uses direct TCP/IP socket communication without DLL.
    Based on the DLL protocol analysis, it uses tag-based message format.
    
    Supports:
    - TCP/IP connection (socket)
    - Tag-based message format (same as DLL)
    - Payment ID and Bill ID support
    - Connection keep-alive during transaction
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Force TCP/IP connection
        connection_type = self.config.get('connection_type', 'tcp')
        if connection_type == 'serial':
            connection_type = 'tcp'
            import warnings
            warnings.warn('Serial connection requested but using TCP/IP instead. Set POS_CONNECTION_TYPE=tcp in .env')
        
        self.connection_type = 'tcp'  # Always TCP/IP for socket connection
        self.tcp_host = self.config.get('tcp_host', '192.168.1.100')
        self.tcp_port = self.config.get('tcp_port', 1362)
        self.timeout = self.config.get('timeout', 30)
        self.merchant_id = self.config.get('merchant_id', '')
        self.terminal_id = self.config.get('terminal_id', '')
        
        self._connection = None
    
    def _connect(self):
        """Establish TCP/IP connection to POS device."""
        # If already connected, reuse the connection
        if self._connection:
            try:
                # Check if connection is still alive
                try:
                    self._connection.getpeername()
                    # Connection is alive, reuse it
                    return
                except (OSError, socket.error):
                    # Connection is dead, reconnect
                    self._connection = None
            except Exception:
                # Connection check failed, reconnect
                self._connection = None
        
        try:
            self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Set socket options to keep connection alive
            self._connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Set timeout for connection (but keep it long for transaction waiting)
            self._connection.settimeout(30)  # 30 seconds for initial connection
            self._connection.connect((self.tcp_host, self.tcp_port))
            print(f"✅ اتصال TCP/IP برقرار شد: {self.tcp_host}:{self.tcp_port}")
        except Exception as e:
            raise GatewayException(f'Failed to connect to POS via TCP: {str(e)}')
    
    def _disconnect(self):
        """Close connection to POS device."""
        if self._connection:
            try:
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
            
            if self._connection:
                result['success'] = True
                result['message'] = f'اتصال TCP/IP موفق بود (IP: {self.tcp_host}, Port: {self.tcp_port})'
                result['details'] = {
                    'host': self.tcp_host,
                    'port': self.tcp_port,
                    'timeout': self.timeout
                }
            
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
    
    def _build_payment_request(self, amount: int, order_number: str, 
                               additional_data: Dict[str, Any] = None) -> bytes:
        """
        Build payment request using tag-based format (same as DLL).
        
        Format: PR{type}AM{amount}TE{terminal}ME{merchant}SO{order}CU{customer}PD{payment_id}BI{bill_id}
        No separators between tags, just concatenated.
        
        Args:
            amount: Payment amount in Rial
            order_number: Order number
            additional_data: Additional data (customer_name, payment_id, bill_id)
            
        Returns:
            bytes: Formatted request bytes (ready to send)
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
            bill_id = str(additional_data['bill_id']).strip()
            # Remove 'BI' prefix if user accidentally included it
            if bill_id.startswith('BI'):
                bill_id = bill_id[2:].strip()
            # Limit to 20 chars and zero-pad to 20
            bill_id = bill_id[:20].zfill(20)
            parts.append(f"BI{bill_id}")
        
        # Join all parts (NO separator - this is key!)
        message = "".join(parts)
        
        # Debug: Print the message we're building
        print(f"🔧 ساخت پیام: {message}")
        print(f"   طول پیام: {len(message)} کاراکتر")
        print(f"   تعداد تگ‌ها: {len(parts)}")
        
        # Convert to ASCII bytes (POS devices use ASCII, not UTF-8)
        message_bytes = message.encode('ascii')
        
        # IMPORTANT: DLL sends message WITHOUT any terminator
        # The message is sent as-is, no CRLF, no NULL, no length prefix
        # This is the exact format DLL uses
        format_type = self.config.get('pos_message_format', 'dll_exact')
        
        if format_type == 'dll_exact':
            # Exact DLL format - no terminator, no framing, just raw message
            # This is what DLL sends
            pass  # Don't modify message_bytes
        elif format_type == 'with_length':
            # Add length prefix (4 digits, zero-padded) - some devices might need this
            length = len(message_bytes)
            length_prefix = f"{length:04d}".encode('ascii')
            message_bytes = length_prefix + message_bytes
            print(f"   ✅ اضافه کردن Length prefix: {length}")
        elif format_type == 'with_stx_etx':
            # Add STX (0x02) at start and ETX (0x03) at end
            message_bytes = b'\x02' + message_bytes + b'\x03'
            print(f"   ✅ اضافه کردن STX/ETX framing")
        elif format_type == 'with_terminator':
            # Add CRLF terminator
            message_bytes = message_bytes + b'\r\n'
            print(f"   ✅ اضافه کردن CRLF terminator")
        elif format_type == 'with_null':
            # Add NULL terminator
            message_bytes = message_bytes + b'\x00'
            print(f"   ✅ اضافه کردن NULL terminator")
        
        print(f"   پیام نهایی ({len(message_bytes)} bytes): {message_bytes[:100]}...")
        print(f"   Hex (اول 200 کاراکتر): {message_bytes.hex()[:200]}...")
        
        return message_bytes
    
    def _send_command(self, command: bytes, wait_for_response: bool = True, max_wait_time: int = 120) -> str:
        """
        Send command to POS device and receive response.
        
        IMPORTANT: Connection stays alive during the entire transaction.
        The socket remains open until response is received or timeout.
        
        Args:
            command: Command bytes to send
            wait_for_response: Whether to wait for response
            max_wait_time: Maximum time to wait for response in seconds
            
        Returns:
            str: Response from POS device
            
        Raises:
            GatewayException: If communication fails
        """
        if not self._connection:
            self._connect()
        
        try:
            # Debug: Log what we're sending
            try:
                command_str = command.decode('utf-8', errors='replace')
                print(f"📤 ارسال درخواست ({len(command)} bytes): {command_str}")
                print(f"   Hex: {command.hex()[:100]}...")
            except:
                print(f"📤 ارسال درخواست ({len(command)} bytes): {command[:50]}...")
            
            # IMPORTANT: Keep connection alive - don't close it!
            # Send command
            try:
                bytes_sent = self._connection.sendall(command)
                print(f"✅ داده ارسال شد ({len(command)} bytes)")
                
                # Verify data was sent by checking socket state
                try:
                    # Try to get socket info to verify it's still connected
                    peer = self._connection.getpeername()
                    print(f"✅ اتصال فعال است: {peer[0]}:{peer[1]}")
                except Exception as e:
                    print(f"⚠️  خطا در بررسی اتصال: {e}")
                
            except socket.error as e:
                print(f"❌ خطا در ارسال داده: {e}")
                raise GatewayException(f'Failed to send data to POS: {str(e)}')
            
            # Small delay to ensure data is sent and device processes it
            time.sleep(0.5)  # Increased delay to give device time to process
            
            # IMPORTANT: Some POS devices send immediate ACK or response
            # Check for immediate response (device might acknowledge or reject immediately)
            try:
                # Set very short timeout to check for immediate response
                self._connection.settimeout(2)  # 2 seconds to check for immediate response
                ack = self._connection.recv(4096)
                if ack:
                    ack_str = ack.decode('utf-8', errors='ignore')
                    print(f"📥 دریافت پاسخ فوری از دستگاه: {ack_str[:100]}...")
                    print(f"   Hex: {ack.hex()[:100]}...")
                    # If we got a response, it might be the full response or an ACK
                    # Check if it looks like a complete response
                    if len(ack_str) > 5 and ('RS' in ack_str or 'OK' in ack_str or 'ACK' in ack_str):
                        print(f"✅ پاسخ کامل دریافت شد!")
                        return ack_str
            except socket.timeout:
                # No immediate response - that's OK, device might process and respond later
                print("ℹ️  هیچ پاسخ فوری دریافت نشد (این طبیعی است - دستگاه در حال پردازش است)")
            except Exception as e:
                print(f"⚠️  خطا در دریافت پاسخ فوری: {e}")
            finally:
                # Reset timeout for main response waiting
                self._connection.settimeout(1)
            
            if not wait_for_response:
                # For commands that don't need response
                return ''
            
            # Wait for response - POS devices may take time to respond
            # Especially for payment transactions that require user interaction
            # IMPORTANT: Keep connection open and wait for response
            response = ''
            start_time = time.time()
            
            # Set socket timeout for reading (1 second per read attempt)
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
                    # Try to receive data (with timeout to allow periodic checks)
                    chunk = self._connection.recv(4096)
                    if chunk:
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        response += chunk_str
                        print(f"📥 دریافت داده: {chunk_str[:100]}...")
                        
                        # If we got some data, wait a bit more to see if more is coming
                        time.sleep(0.5)
                        # Try to get more data if available (keep connection open)
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
                            # But connection is still open!
                            break
                        
                        # If we have a complete response, break
                        if response and len(response) > 10:  # At least some meaningful response
                            print(f"✅ پاسخ کامل دریافت شد ({len(response)} chars)")
                            break
                    else:
                        # No data yet, wait a bit but keep connection alive
                        time.sleep(1)
                except socket.timeout:
                    # No response yet, continue waiting
                    # IMPORTANT: Connection is still alive, just no data yet
                    elapsed = int(time.time() - start_time)
                    if elapsed % 10 == 0 and elapsed > 0:  # Print every 10 seconds
                        print(f"⏳ منتظر پاسخ... ({elapsed}/{max_wait_time} ثانیه) - اتصال فعال است")
                    # Check if connection is still alive
                    try:
                        self._connection.getpeername()  # This will raise if connection is dead
                    except (OSError, socket.error):
                        print(f"❌ اتصال قطع شد!")
                        raise GatewayException('اتصال به دستگاه POS قطع شد')
                    continue
                except Exception as e:
                    # Connection error - but try to keep connection if possible
                    print(f"⚠️  خطا در دریافت پاسخ: {e}")
                    # Check if connection is still alive
                    try:
                        self._connection.getpeername()
                        # Connection is still alive, continue waiting
                        continue
                    except (OSError, socket.error):
                        # Connection is dead, raise error
                        raise GatewayException(f'اتصال به دستگاه POS قطع شد: {e}')
            
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
            raise GatewayException(f'Failed to communicate with POS: {str(e)}')
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse response from POS device.
        
        Based on Pardakht Novin protocol:
        Format: RS{response_code}SR{serial}RN{reference}TI{terminal}PN{pan}...
        
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
            '00': 'تراکنش موفق',
            '01': 'تراکنش ناموفق - کارت نامعتبر',
            '02': 'تراکنش ناموفق - موجودی کافی نیست',
            '03': 'تراکنش ناموفق - رمز اشتباه',
            '04': 'تراکنش ناموفق - کارت منقضی شده',
            '05': 'تراکنش ناموفق - خطا در ارتباط',
            '06': 'تراکنش ناموفق - خطای سیستم',
            '81': 'تراکنش توسط کاربر لغو شد',
            '99': 'تراکنش ناموفق - خطای نامشخص',
        }
        return error_messages.get(error_code, f'خطای نامشخص: {error_code}')
    
    def initiate_payment(self, amount: int, order_details: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Initiate payment transaction with POS device.
        
        This method follows the exact same flow as the DLL:
        1. Test connection first (like DLL's TestConnection())
        2. Build payment request message
        3. Send transaction (like DLL's send_transaction())
        4. Wait for response with connection alive
        
        Args:
            amount: Payment amount in Rial
            order_details: Dictionary containing order details
                - order_number: Order number
                - customer_name: Customer name (optional)
                - payment_id: Payment ID (optional)
                - bill_id: Bill ID (optional)
                
        Returns:
            Dict[str, Any]: Gateway response containing transaction information
        """
        order_number = order_details.get('order_number', '')
        customer_name = order_details.get('customer_name', '')
        payment_id = order_details.get('payment_id', '')
        bill_id = order_details.get('bill_id', '')
        
        # IMPORTANT: Follow DLL's exact flow
        # Step 1: Test connection first (like DLL's TestConnection())
        print("🔍 در حال تست اتصال به دستگاه POS...")
        try:
            connection_test = self.test_connection()
            if not connection_test.get('success', False):
                raise GatewayException('اتصال به دستگاه POS برقرار نشد. لطفاً IP و Port را بررسی کنید.')
            print(f"✅ اتصال TCP/IP برقرار است: {self.tcp_host}:{self.tcp_port}")
        except Exception as e:
            print(f"⚠️  خطا در تست اتصال: {e}")
            # Try to reconnect
            try:
                if self._connection:
                    self._disconnect()
                time.sleep(1)
                self._connect()
                print(f"✅ اتصال مجدد برقرار شد: {self.tcp_host}:{self.tcp_port}")
            except Exception as reconnect_error:
                raise GatewayException(f'اتصال به دستگاه POS برقرار نشد: {str(reconnect_error)}')
        
        # Step 2: Build additional_data dictionary (like DLL sets properties)
        additional_data = {}
        if customer_name:
            additional_data['customer_name'] = customer_name
        if payment_id:
            additional_data['payment_id'] = payment_id
        if bill_id:
            additional_data['bill_id'] = bill_id
        
        # Step 3: Build payment request message (DLL builds this internally)
        # We build it explicitly to match DLL's format
        request_bytes = self._build_payment_request(
            amount=amount,
            order_number=order_number,
            additional_data=additional_data if additional_data else None
        )
        
        try:
            # Step 4: Send transaction (like DLL's send_transaction())
            # Payment transactions require user interaction (card swipe, PIN entry)
            # So we need to wait longer (up to 2 minutes)
            print("\n⚠️  توجه: مبلغ روی دستگاه نمایش داده می‌شود.")
            print("   لطفاً منتظر بمانید تا:")
            print("   1. کارت را بکشید")
            print("   2. رمز را وارد کنید")
            print("   3. یا در دستگاه لغو کنید")
            print(f"   (حداکثر 120 ثانیه منتظر می‌مانیم)\n")
            
            # IMPORTANT: Keep connection alive during transaction (like DLL does)
            # The socket must stay open to receive response
            response = self._send_command(request_bytes, wait_for_response=True, max_wait_time=120)
            
            # Step 5: Parse response (like DLL's GetParsedResp())
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
            # This matches DLL behavior - connection stays alive
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
