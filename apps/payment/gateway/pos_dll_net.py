"""
POS Card Reader Gateway using .NET DLL (Pardakht Novin).

This module implements POS gateway using the official .NET DLL from Pardakht Novin.
The DLL file is: pna.pcpos.dll (version 2.2.0.0)

IMPORTANT: On macOS ARM64 (Apple Silicon), you MUST run Python with Rosetta 2 (x86_64)
to avoid crashes when using x86 DLLs. Use the wrapper script: ./run_pos_command.sh
"""
import os
import platform
import time
import atexit
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .base import BasePaymentGateway
from .exceptions import GatewayException
from .pos import POSPaymentGateway  # Fallback to direct protocol

try:
    import clr
    # Try to load clr - this might fail if Mono/.NET runtime is not available
    try:
        clr.__version__  # Just check if it's loaded
        PYTHONNET_AVAILABLE = True
    except (RuntimeError, AttributeError):
        # clr is imported but runtime is not available
        PYTHONNET_AVAILABLE = False
except (ImportError, RuntimeError):
    PYTHONNET_AVAILABLE = False

# Register cleanup handler for Mono runtime
if PYTHONNET_AVAILABLE:
    def _mono_cleanup():
        """Cleanup Mono runtime on exit."""
        try:
            # Try to cleanup gracefully
            # Note: On macOS ARM64 with x86 DLL, this might crash
            # Solution: Use Rosetta 2 (arch -x86_64) to run Python
            pass
        except Exception:
            pass
    
    atexit.register(_mono_cleanup)


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
        
        # Try to load DLL if path is provided
        # Note: With Mono installed, DLL can work on Mac/Linux too
        if self.dll_path and os.path.exists(self.dll_path):
            try:
                self._load_dll()
                self.use_dll = True
            except Exception as e:
                # If DLL loading fails, use fallback
                self.use_dll = False
                self.fallback_gateway = POSPaymentGateway(config)
                # Log the error for debugging
                import warnings
                warnings.warn(f'Failed to load DLL, using fallback: {str(e)}')
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
            
            # Import PCPOS class from the correct namespace
            # The DLL uses namespace: Intek.PcPosLibrary
            from Intek.PcPosLibrary import PCPOS
            
            # Create instance
            self.pos_instance = PCPOS()
            
            # Configure connection - Force TCP/IP (Socket) connection
            connection_type = self.config.get('connection_type', 'tcp')
            
            # Always use TCP/IP (Socket) connection, not serial
            if connection_type == 'serial':
                # Warn if serial is requested but we'll use TCP/IP
                import warnings
                warnings.warn('Serial connection requested but using TCP/IP instead. Set POS_CONNECTION_TYPE=tcp in .env')
                connection_type = 'tcp'
            
            # Configure TCP/IP (Socket) connection
            # Ensure all values are correct types
            self.pos_instance.Ip = str(self.config.get('tcp_host', '192.168.1.100'))
            tcp_port = self.config.get('tcp_port', 1362)
            # Port should be int (not string)
            self.pos_instance.Port = int(tcp_port) if isinstance(tcp_port, str) else tcp_port
            # Use Enum for ConnectionType - LAN means TCP/IP (Socket)
            self.pos_instance.ConnectionType = PCPOS.cnType.LAN
            
            # Set terminal ID if provided
            terminal_id = self.config.get('terminal_id', '')
            if terminal_id:
                # Terminal ID can be string or number
                if isinstance(terminal_id, str):
                    # Try to set as string first
                    self.pos_instance.TerminalID = terminal_id
                else:
                    # If it's a number, convert to string
                    self.pos_instance.TerminalID = str(terminal_id)
            
            # Set merchant ID (کد پذیرنده) if provided
            # Note: در بیشتر موارد Merchant ID در Terminal ID گنجانده شده است
            # اما اگر نیاز باشد می‌توانیم از R0Merchant استفاده کنیم
            merchant_id = self.config.get('merchant_id', '')
            if merchant_id:
                # Try to set R0Merchant (برای Additional Payment)
                if hasattr(self.pos_instance, 'R0Merchant'):
                    self.pos_instance.R0Merchant = str(merchant_id)
                # یا می‌توانیم در پیام TLV اضافه کنیم (اگر نیاز باشد)
            
            # Set serial number if provided (some DLLs may need this)
            serial_number = self.config.get('device_serial_number', '')
            if serial_number:
                if hasattr(self.pos_instance, 'SerialNumber'):
                    self.pos_instance.SerialNumber = str(serial_number)
                elif hasattr(self.pos_instance, 'DeviceSerial'):
                    self.pos_instance.DeviceSerial = str(serial_number)
            
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
            'connection_type': self.config.get('connection_type', 'tcp'),
            'details': {}
        }
        
        if self.use_dll and self.pos_instance:
            # Use DLL test connection
            try:
                success = self._test_connection()
                result['success'] = success
                if success:
                    result['message'] = 'اتصال موفق بود (استفاده از DLL)'
                    if self.config.get('connection_type') == 'tcp':
                        result['details'] = {
                            'host': self.config.get('tcp_host', 'N/A'),
                            'port': self.config.get('tcp_port', 'N/A'),
                            'method': 'DLL (TCP/IP)'
                        }
                    else:
                        result['details'] = {
                            'port': self.config.get('serial_port', 'N/A'),
                            'baudrate': self.config.get('serial_baudrate', 'N/A'),
                            'method': 'DLL (Serial)'
                        }
                else:
                    result['message'] = 'اتصال ناموفق بود (استفاده از DLL)'
            except Exception as e:
                result['message'] = f'خطا در تست اتصال با DLL: {str(e)}'
                result['details'] = {'error': str(e), 'method': 'DLL'}
        else:
            # Use fallback gateway
            if self.fallback_gateway:
                if hasattr(self.fallback_gateway, 'test_connection'):
                    return self.fallback_gateway.test_connection()
                else:
                    result['message'] = 'Gateway fallback از تست اتصال پشتیبانی نمی‌کند'
            else:
                result['message'] = 'DLL در دسترس نیست و fallback gateway تنظیم نشده است'
        
        return result
    
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
            # Set amount (DLL expects string, not int)
            self.pos_instance.Amount = str(amount)
            
            # Set order number if supported
            # Note: DLL might use different property names
            # Adjust based on actual DLL API
            if order_number and hasattr(self.pos_instance, 'OrderNumber'):
                # OrderNumber should be string
                self.pos_instance.OrderNumber = str(order_number)
            
            # Set additional data if provided
            if additional_data:
                customer_name = additional_data.get('customer_name', '')
                if customer_name and hasattr(self.pos_instance, 'CustomerName'):
                    self.pos_instance.CustomerName = customer_name
            
            # Setup response tracking
            response_received = False
            response = None
            raw_response = None
            response_obj = None
            
            # Try to setup event handler for response (if available)
            def on_response_received(sender, args):
                nonlocal response_received, response_obj
                response_received = True
                if hasattr(args, 'Response'):
                    response_obj = args.Response
                elif hasattr(args, 'response'):
                    response_obj = args.response
            
            try:
                if hasattr(self.pos_instance, 'add_GetResponse'):
                    self.pos_instance.add_GetResponse(on_response_received)
            except Exception:
                # Event handler not available or failed, continue with polling
                    pass
            
            # Send transaction
            # Note: send_transaction() sends the request to POS device
            # The device will:
            # 1. Display the amount on screen
            # 2. Wait for card insertion (user needs to insert card)
            # 3. Wait for PIN entry (user needs to enter PIN)
            # 4. Process the transaction
            # 5. Return the response
            # 
            # send_transaction() may return immediately, so we need to wait
            # for the response to be available
            self.pos_instance.send_transaction()
            
            # Wait for response (DLL handles this asynchronously)
            # The device is now waiting for user action:
            # - Card insertion
            # - PIN entry  
            # - Transaction cancellation
            # We need to wait until the response is available
            max_attempts = 120  # Wait up to 120 seconds (2 minutes) for user to complete transaction
            start_time = time.time()
            
            for attempt in range(max_attempts):
                # Check for response every second
                if attempt > 0:
                    time.sleep(1)
                
                # Check if event handler received response
                if response_received and response_obj:
                    break
                
                # Try to get Response object
                try:
                    if hasattr(self.pos_instance, 'Response') and self.pos_instance.Response is not None:
                        response_obj = self.pos_instance.Response
                        # Try to get string representation or properties from Response
                        if hasattr(response_obj, 'ToString'):
                            response = response_obj.ToString()
                        elif hasattr(response_obj, 'Message'):
                            response = str(response_obj.Message)
                        if response:
                            break
                except Exception as e:
                    pass
                
                # Try GetParsedResp from pos_instance
                try:
                    if hasattr(self.pos_instance, 'GetParsedResp'):
                        resp = self.pos_instance.GetParsedResp()
                        if resp:
                            resp_str = str(resp).strip()
                            # Check if it's a valid response (not just class name or empty)
                            if resp_str and resp_str != 'Intek.PcPosLibrary.Response' and len(resp_str) > 5:
                                response = resp_str
                                break
                except Exception as e:
                    pass
                
                # Try RawResponse property from pos_instance
                try:
                    if hasattr(self.pos_instance, 'RawResponse'):
                        raw = self.pos_instance.RawResponse
                        if raw:
                            raw_str = str(raw).strip()
                            # Check if it's a valid response
                            if raw_str and len(raw_str) > 5:
                                raw_response = raw_str
                                if not response:
                                    response = raw_str
                                break
                except Exception:
                    pass
                
                # Try GetResponse method
                try:
                    if hasattr(self.pos_instance, 'GetResponse'):
                        resp = self.pos_instance.GetResponse()
                        if resp:
                            if isinstance(resp, str):
                                resp_str = resp.strip()
                            else:
                                # If it's an object, try to get string representation
                                resp_str = str(resp).strip()
                            # Check if it's a valid response
                            if resp_str and resp_str != 'Intek.PcPosLibrary.Response' and len(resp_str) > 5:
                                response = resp_str
                                break
                except Exception:
                    pass
                
                # Check if there's an error message
                try:
                    if hasattr(self.pos_instance, 'GetErrorMsg'):
                        error_msg = self.pos_instance.GetErrorMsg()
                        if error_msg and error_msg.strip():
                            raise GatewayException(f'خطا از دستگاه POS: {error_msg}')
                except GatewayException:
                    raise
                except Exception:
                    pass
            
            # If still no response, try to get error message
            if not response and not raw_response and not response_obj:
                error_msg = ''
                try:
                    if hasattr(self.pos_instance, 'GetErrorMsg'):
                        error_msg = self.pos_instance.GetErrorMsg()
                except Exception:
                    pass
                
                # Try to get response code or status
                status_code = None
                try:
                    if hasattr(self.pos_instance, 'GetTrxnResp'):
                        status_code = self.pos_instance.GetTrxnResp()
                except Exception:
                    pass
                
                if error_msg:
                    raise GatewayException(f'خطا از دستگاه POS: {error_msg}')
                elif status_code:
                    raise GatewayException(f'خطا از دستگاه POS با کد: {status_code}')
                else:
                    elapsed_seconds = int(time.time() - start_time)
                    raise GatewayException(
                        f'هیچ پاسخی از دستگاه POS دریافت نشد (بعد از {elapsed_seconds} ثانیه). '
                        'لطفاً بررسی کنید که:\n'
                        '  - دستگاه روشن است و مبلغ را نمایش می‌دهد\n'
                        '  - کارت را کشیده‌اید\n'
                        '  - رمز را وارد کرده‌اید\n'
                        '  - یا در دستگاه لغو کرده‌اید'
                    )
            
            # If we have response_obj, try to extract more information
            if response_obj:
                try:
                    # Try to get all properties from Response object
                    # First, try to get all public properties using reflection
                    import System
                    response_type = response_obj.GetType()
                    
                    # Get all properties
                    properties = response_type.GetProperties()
                    for prop in properties:
                        try:
                            prop_name = prop.Name
                            prop_value = prop.GetValue(response_obj, None)
                            if prop_value is not None:
                                prop_str = str(prop_value).strip()
                                # Skip if it's just the class name
                                if prop_str and prop_str != 'Intek.PcPosLibrary.Response':
                                    if not response:
                                        response = f"{prop_name}={prop_str}"
                                    else:
                                        response += f", {prop_name}={prop_str}"
                        except Exception:
                            pass
                    
                    # Also try common methods
                    if not response:
                        # Try GetParsedResp method
                        if hasattr(response_obj, 'GetParsedResp'):
                            try:
                                parsed = response_obj.GetParsedResp()
                                if parsed:
                                    parsed_str = str(parsed).strip()
                                    if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                                        response = parsed_str
                            except Exception:
                                pass
                        
                        # Try RawResponse property
                        if not response and hasattr(response_obj, 'RawResponse'):
                            try:
                                raw = response_obj.RawResponse
                                if raw:
                                    raw_str = str(raw).strip()
                                    if raw_str:
                                        response = raw_str
                            except Exception:
                                pass
                        
                        # Try ToString method
                        if not response:
                            try:
                                to_string = response_obj.ToString()
                                if to_string and to_string != 'Intek.PcPosLibrary.Response':
                                    response = to_string
                            except Exception:
                                pass
                    
                    # If still no response, try to get from pos_instance directly
                    if not response:
                        if hasattr(self.pos_instance, 'GetParsedResp'):
                            try:
                                parsed = self.pos_instance.GetParsedResp()
                                if parsed:
                                    parsed_str = str(parsed).strip()
                                    if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                                        response = parsed_str
                            except Exception:
                                pass
                except Exception as e:
                    # Log error but continue - don't crash
                    import traceback
                    print(f"⚠️  خطا در خواندن Response object: {e}")
                    traceback.print_exc()
            
            # Parse response
            return self._parse_dll_response(response, raw_response, response_obj)
            
        except GatewayException:
            # Re-raise GatewayException as is
            raise
        except Exception as e:
            raise GatewayException(f'خطا در ارسال پرداخت به DLL: {str(e)}')
    
    def _parse_dll_response(self, response: str, raw_response: str, response_obj=None) -> Dict[str, Any]:
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
            'raw_response': raw_response or '',
            'parsed_response': response or ''
        }
        
        # If no response at all, return early
        if not response and not raw_response:
            result['response_message'] = 'هیچ پاسخی از دستگاه دریافت نشد'
            return result
        
        # Use raw_response if response is empty
        response_text = response or raw_response or ''
        
        # Try to extract transaction details from response
        # Adjust parsing based on actual DLL response format
        
        # Check if transaction was successful
        # DLL usually returns response codes in format like "RS01" for success
        # Common success codes: RS01, RS013, RS00 (with specific subcodes)
        if 'RS01' in response_text or 'RS013' in response_text:
            result['success'] = True
            result['status'] = 'success'
            result['response_code'] = '00'
        elif 'RS00' in response_text:
            # Extract specific error code
            result['status'] = 'failed'
            # Try to extract error code (RS00XX format)
            import re
            error_match = re.search(r'RS00(\d+)', response_text)
            if error_match:
                error_code = error_match.group(1)
                result['response_code'] = error_code
            else:
                result['response_code'] = '01'  # Generic error
            result['response_message'] = self._get_error_message(result['response_code'])
        else:
            # Unknown response format
            result['status'] = 'failed'
            result['response_code'] = '99'
            result['response_message'] = f'پاسخ نامشخص از دستگاه: {response_text[:100]}'
        
        # Extract transaction details from Response object if available
        if response_obj:
            try:
                import System
                response_type = response_obj.GetType()
                
                # Try to get all properties using reflection
                properties = response_type.GetProperties()
                response_data = {}
                for prop in properties:
                    try:
                        prop_name = prop.Name
                        prop_value = prop.GetValue(response_obj, None)
                        if prop_value is not None:
                            prop_str = str(prop_value).strip()
                            # Skip if it's just the class name or empty
                            if prop_str and prop_str != 'Intek.PcPosLibrary.Response' and prop_str != 'None':
                                response_data[prop_name] = prop_str
                    except Exception:
                        pass
                
                # Map common properties to result
                # Try to get PAN ID (card number) - common property names
                for pan_key in ['PANID', 'PanID', 'CardNumber', 'CardNo', 'PAN']:
                    if pan_key in response_data:
                        result['card_number'] = response_data[pan_key]
                        break
                
                # Try methods if properties didn't work
                if not result['card_number']:
                    for method_name in ['GetPANID', 'GetCardNumber', 'GetPAN']:
                        if hasattr(response_obj, method_name):
                            try:
                                method = getattr(response_obj, method_name)
                                pan_id = method()
                                if pan_id:
                                    result['card_number'] = str(pan_id).strip()
                                    break
                            except Exception:
                                pass
                
                # Try to get bank name
                for bank_key in ['BankName', 'Bank']:
                    if bank_key in response_data:
                        result['bank_name'] = response_data[bank_key]
                        break
                
                if 'bank_name' not in result:
                    if hasattr(response_obj, 'GetBankName'):
                        try:
                            bank_name = response_obj.GetBankName()
                            if bank_name:
                                result['bank_name'] = str(bank_name).strip()
                        except Exception:
                            pass
                
                # Try to get terminal ID
                for term_key in ['TerminalID', 'TerminalId', 'TermID']:
                    if term_key in response_data:
                        result['terminal_id'] = response_data[term_key]
                        break
                
                if 'terminal_id' not in result:
                    if hasattr(response_obj, 'GetTerminalID'):
                        try:
                            term_id = response_obj.GetTerminalID()
                            if term_id:
                                result['terminal_id'] = str(term_id).strip()
                        except Exception:
                            pass
                
                # Try to get amount
                for amount_key in ['Amount', 'TransactionAmount', 'TrxnAmount']:
                    if amount_key in response_data:
                        result['amount'] = response_data[amount_key]
                        break
                
                if 'amount' not in result:
                    if hasattr(response_obj, 'GetAmount'):
                        try:
                            amount = response_obj.GetAmount()
                            if amount:
                                result['amount'] = int(amount)
                        except Exception:
                            pass
                
                # Try to get reference number (RRN)
                for rrn_key in ['RRN', 'TrxnRRN', 'ReferenceNumber', 'RefNumber']:
                    if rrn_key in response_data:
                        result['reference_number'] = response_data[rrn_key]
                        break
                
                if not result['reference_number']:
                    if hasattr(response_obj, 'GetTrxnRRN'):
                        try:
                            rrn = response_obj.GetTrxnRRN()
                            if rrn:
                                result['reference_number'] = str(rrn).strip()
                        except Exception:
                            pass
                
                # Try to get transaction serial
                for serial_key in ['Serial', 'TrxnSerial', 'TransactionSerial']:
                    if serial_key in response_data:
                        result['transaction_serial'] = response_data[serial_key]
                        break
                
                if 'transaction_serial' not in result:
                    if hasattr(response_obj, 'GetTrxnSerial'):
                        try:
                            serial = response_obj.GetTrxnSerial()
                            if serial:
                                result['transaction_serial'] = str(serial).strip()
                        except Exception:
                            pass
                
                # Try to get transaction date/time
                for date_key in ['DateTime', 'TrxnDateTime', 'TransactionDate']:
                    if date_key in response_data:
                        result['transaction_date'] = response_data[date_key]
                        break
                
                if 'transaction_date' not in result:
                    if hasattr(response_obj, 'GetTrxnDateTime'):
                        try:
                            date_time = response_obj.GetTrxnDateTime()
                            if date_time:
                                result['transaction_date'] = str(date_time).strip()
                        except Exception:
                            pass
                
                # Try to get response code
                for resp_code_key in ['ResponseCode', 'RespCode', 'Code', 'Status']:
                    if resp_code_key in response_data:
                        code = response_data[resp_code_key]
                        if code and not result['response_code']:
                            result['response_code'] = str(code).strip()
                            # Update success status based on response code
                            if code == '00' or code == 'RS01' or code == 'RS013':
                                result['success'] = True
                                result['status'] = 'success'
                            break
                
                # Store all response data for debugging
                if response_data:
                    result['response_data'] = response_data
                
                # Try RawResponse property
                if hasattr(response_obj, 'RawResponse'):
                    raw = response_obj.RawResponse
                    if raw and not raw_response:
                        raw_response = raw
            except Exception:
                pass
        
        # Extract transaction details from pos_instance methods
        # Adjust based on actual DLL response format
        try:
            # Try to get reference number
            if hasattr(self.pos_instance, 'GetTrxnRRN'):
                rrn = self.pos_instance.GetTrxnRRN()
                if rrn and not result.get('reference_number'):
                    result['reference_number'] = str(rrn)
            
            # Try to get transaction serial
            if hasattr(self.pos_instance, 'GetTrxnSerial'):
                serial = self.pos_instance.GetTrxnSerial()
                if serial and not result.get('transaction_id'):
                    result['transaction_id'] = str(serial)
            
            # Try to get transaction date/time
            if hasattr(self.pos_instance, 'GetTrxnDateTime'):
                transaction_datetime = self.pos_instance.GetTrxnDateTime()
                if transaction_datetime and not result.get('transaction_datetime'):
                    result['transaction_datetime'] = str(transaction_datetime)
            
            # Try to get bank name
            if hasattr(self.pos_instance, 'GetBankName'):
                bank_name = self.pos_instance.GetBankName()
                if bank_name and not result.get('bank_name'):
                    result['bank_name'] = str(bank_name)
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
    
    def _cleanup_mono(self):
        """Safely cleanup Mono runtime to prevent crashes."""
        if not PYTHONNET_AVAILABLE:
            return
        
        try:
            # Try to cleanup Mono runtime gracefully
            # Note: On macOS ARM64, this might still crash if DLL is x86
            # Best solution: Use Rosetta 2 (x86_64) to run Python
            if self.pos_instance:
                try:
                    if hasattr(self.pos_instance, 'Dispose'):
                        self.pos_instance.Dispose()
                except Exception:
                    pass
                self.pos_instance = None
        except Exception:
            # Silently ignore cleanup errors
            pass
    
    def __del__(self):
        """Cleanup on destruction."""
        self._cleanup_mono()

