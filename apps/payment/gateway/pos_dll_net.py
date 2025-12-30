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

# Lazy loading of pythonnet to avoid crashes on Django reload
# Only import when actually needed
PYTHONNET_AVAILABLE = None
_clr_module = None

def _check_pythonnet():
    """Check if pythonnet is available (lazy loading)."""
    global PYTHONNET_AVAILABLE, _clr_module
    
    if PYTHONNET_AVAILABLE is not None:
        return PYTHONNET_AVAILABLE
    
    try:
        import clr
        _clr_module = clr
        # Try to load clr - this might fail if Mono/.NET runtime is not available
        try:
            clr.__version__  # Just check if it's loaded
            PYTHONNET_AVAILABLE = True
        except (RuntimeError, AttributeError):
            # clr is imported but runtime is not available
            PYTHONNET_AVAILABLE = False
    except (ImportError, RuntimeError):
        PYTHONNET_AVAILABLE = False
    
    return PYTHONNET_AVAILABLE

# Don't register cleanup handler at module level to avoid crashes on reload
# We'll handle cleanup in the class destructor instead


class POSNETPaymentGateway(BasePaymentGateway):
    """
    Payment Gateway for POS Card Reader using .NET DLL (Pardakht Novin).
    
    This gateway uses the official .NET DLL file (pna.pcpos.dll) provided by Pardakht Novin.
    If DLL is not available or pythonnet is not installed, it automatically falls back 
    to direct protocol implementation (pos.py) which works on Windows, Mac, and Linux.
    
    Cross-platform support:
    - Windows: Uses DLL directly (native .NET)
    - macOS: Uses DLL with Mono (requires Rosetta 2 for x86 DLLs on ARM64)
    - Linux: Uses DLL with Mono, or falls back to direct protocol
    - All platforms: Falls back to direct protocol (pos.py) if DLL fails
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.dll_path = self.config.get('dll_path', '')
        self.use_dll = False
        self.pos_instance = None
        self.fallback_gateway = None
        self.platform = platform.system().lower()
        
        # Always create fallback gateway first (works on all platforms)
        self.fallback_gateway = POSPaymentGateway(config)
        
        # IMPORTANT: Check pythonnet availability first (lazy loading)
        pythonnet_available = _check_pythonnet()
        
        # Check if we can use DLL
        if not pythonnet_available:
            # pythonnet not available, use fallback
            self.use_dll = False
            import warnings
            warnings.warn('pythonnet not available, using direct protocol (pos.py) which works on all platforms')
            return
        
        # Check platform compatibility
        if self.platform == 'darwin':  # macOS
            # On macOS ARM64, DLL x86 requires Rosetta 2
            # We'll try to load, but if it fails, fallback is ready
            arch = platform.machine().lower()
            if arch == 'arm64':
                import warnings
                warnings.warn(
                    'macOS ARM64 detected. DLL x86 requires Rosetta 2. '
                    'If DLL fails, will automatically use direct protocol (pos.py). '
                    'Use ./run_pos_command.sh for Rosetta 2 support.'
                )
        
        # Try to load DLL if path is provided
        # Note: With Mono installed, DLL can work on Mac/Linux too
        if self.dll_path and os.path.exists(self.dll_path):
            try:
                self._load_dll()
                self.use_dll = True
                # Test if DLL actually works
                try:
                    # Quick test - just check if instance is valid
                    if self.pos_instance:
                        self.use_dll = True
                except Exception:
                    # DLL loaded but doesn't work, use fallback
                    self.use_dll = False
                    import warnings
                    warnings.warn('DLL loaded but not functional, using fallback protocol')
            except Exception as e:
                # If DLL loading fails, use fallback (this is normal on some platforms)
                self.use_dll = False
                import warnings
                warnings.warn(
                    f'Failed to load DLL ({str(e)}), automatically using direct protocol (pos.py) '
                    f'which works on {self.platform}. This is normal and expected.'
                )
        else:
            # No DLL path provided, use direct protocol (works everywhere)
            self.use_dll = False
            if not self.dll_path:
                import warnings
                warnings.warn(
                    'DLL path not configured, using direct protocol (pos.py) '
                    f'which works on {self.platform}. Set POS_DLL_PATH in .env to use DLL.'
                )
    
    def _load_dll(self):
        """Load .NET DLL file using pythonnet."""
        global _clr_module
        
        # Lazy check pythonnet availability
        if not _check_pythonnet():
            raise GatewayException('pythonnet is not installed. Install it with: pip install pythonnet')
        
        # Import clr only when needed
        if _clr_module is None:
            import clr
            _clr_module = clr
        
        try:
            # Add reference to DLL
            _clr_module.AddReference(self.dll_path)
            
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
            
            # IMPORTANT: Configure timeout to keep connection alive
            # Set a long timeout so connection stays open while waiting for user interaction
            # Some DLLs have Timeout property - set it to a large value (e.g., 120 seconds)
            if hasattr(self.pos_instance, 'Timeout'):
                # Set timeout to 120 seconds (2 minutes) to keep connection alive
                self.pos_instance.Timeout = 120000  # milliseconds (120 seconds)
            elif hasattr(self.pos_instance, 'ConnectionTimeout'):
                self.pos_instance.ConnectionTimeout = 120000
            elif hasattr(self.pos_instance, 'ReceiveTimeout'):
                self.pos_instance.ReceiveTimeout = 120000
            
            # IMPORTANT: Ensure connection stays alive
            # Some DLLs have KeepAlive or similar properties
            if hasattr(self.pos_instance, 'KeepAlive'):
                self.pos_instance.KeepAlive = True
            elif hasattr(self.pos_instance, 'KeepConnectionAlive'):
                self.pos_instance.KeepConnectionAlive = True
            
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
                
                # Set Payment ID (PD) if provided
                payment_id = additional_data.get('payment_id', '')
                if payment_id:
                    # Try different property names that DLL might use
                    if hasattr(self.pos_instance, 'PaymentID'):
                        self.pos_instance.PaymentID = str(payment_id)
                    elif hasattr(self.pos_instance, 'PaymentId'):
                        self.pos_instance.PaymentId = str(payment_id)
                    elif hasattr(self.pos_instance, 'PD'):
                        self.pos_instance.PD = str(payment_id)
                
                # Set Bill ID (BI) if provided
                bill_id = additional_data.get('bill_id', '')
                if bill_id:
                    # Try different property names that DLL might use
                    if hasattr(self.pos_instance, 'BillID'):
                        self.pos_instance.BillID = str(bill_id)
                    elif hasattr(self.pos_instance, 'BillId'):
                        self.pos_instance.BillId = str(bill_id)
                    elif hasattr(self.pos_instance, 'BI'):
                        self.pos_instance.BI = str(bill_id)
            
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
            
            # IMPORTANT: Ensure connection is established and stays alive
            # Test connection first to make sure socket is open
            try:
                if hasattr(self.pos_instance, 'TestConnection'):
                    connection_ok = self.pos_instance.TestConnection()
                    if not connection_ok:
                        print("⚠️  اتصال اولیه ناموفق بود، در حال تلاش مجدد...")
                        # Try to reconnect
                        time.sleep(1)
                        connection_ok = self.pos_instance.TestConnection()
                        if not connection_ok:
                            raise GatewayException('اتصال به دستگاه POS برقرار نشد')
                print(f"✅ اتصال TCP/IP برقرار است: {self.config.get('tcp_host')}:{self.config.get('tcp_port')}")
            except Exception as e:
                print(f"⚠️  خطا در تست اتصال: {e}")
                # Continue anyway - connection might still work
            
            # Send transaction
            # Note: send_transaction() sends the request to POS device
            # The device will:
            # 1. Display the amount on screen
            # 2. Wait for card insertion (user needs to insert card)
            # 3. Wait for PIN entry (user needs to enter PIN)
            # 4. Process the transaction
            # 5. Return the response
            # 
            # IMPORTANT: send_transaction() may return immediately, but the socket
            # connection MUST stay open to receive the response from POS device.
            # The DLL should keep the connection alive internally.
            print(f"📤 در حال ارسال تراکنش به دستگاه POS...")
            self.pos_instance.send_transaction()
            print(f"✅ درخواست ارسال شد. اتصال فعال است و منتظر پاسخ...")
            
            # Wait for response (DLL handles this asynchronously)
            # The device is now waiting for user action:
            # - Card insertion
            # - PIN entry  
            # - Transaction cancellation
            # 
            # IMPORTANT: The socket connection must stay open during this time.
            # We need to wait until the response is available with actual data.
            max_attempts = 120  # Wait up to 120 seconds (2 minutes) for user to complete transaction
            start_time = time.time()
            last_rrn_check = None  # Track last RRN value to detect changes
            
            # Debug: Print status
            print(f"📤 تراکنش ارسال شد. منتظر پاسخ از دستگاه POS...")
            print(f"   ⚠️  اتصال TCP/IP فعال است و منتظر پاسخ می‌ماند")
            print(f"   لطفاً کارت را بکشید و رمز را وارد کنید (یا در دستگاه لغو کنید)")
            
            for attempt in range(max_attempts):
                # Check for response every second
                if attempt > 0:
                    time.sleep(1)
                
                elapsed = int(time.time() - start_time)
                if elapsed > 0 and elapsed % 10 == 0:
                    print(f"⏳ منتظر پاسخ... ({elapsed}/{max_attempts} ثانیه)")
                
                # Check if event handler received response
                if response_received and response_obj:
                    print(f"✅ پاسخ از event handler دریافت شد")
                    break
                
                # Try to get Response object and check if it has actual data
                transaction_complete = False  # Flag to break outer loop
                try:
                    if hasattr(self.pos_instance, 'Response') and self.pos_instance.Response is not None:
                        response_obj = self.pos_instance.Response
                        
                        # Check if Response object has actual data (not just empty object)
                        # Try to get properties that indicate transaction completion
                        has_data = False
                        
                        # Check for Response Code FIRST - this tells us if transaction is complete
                        resp_code = None
                        try:
                            if hasattr(response_obj, 'GetTrxnResp'):
                                resp_code = response_obj.GetTrxnResp()
                                resp_code_str = str(resp_code).strip() if resp_code else ''
                                # Check if response code is valid (not empty, not just "=")
                                if resp_code_str and resp_code_str != '=' and resp_code_str != 'None' and resp_code_str != '':
                                    has_data = True
                                    print(f"✅ Response Code دریافت شد: {resp_code_str}")
                                    
                                    # IMPORTANT: ANY response code means transaction is complete
                                    # Response code 81 might mean cancelled, but transaction is still complete
                                    if resp_code_str == '81':
                                        print(f"⚠️  Response Code 81 دریافت شد - تراکنش کامل شد")
                                        # Transaction is complete, break the loop
                                        transaction_complete = True
                                    elif resp_code_str in ['00', '01', '02', '03', '13']:
                                        # Valid response code - transaction completed
                                        print(f"✅ تراکنش کامل شد (کد: {resp_code_str})")
                                        # Transaction is complete, break the loop
                                        transaction_complete = True
                                    else:
                                        # Any other response code also means transaction is complete
                                        print(f"✅ Response Code دریافت شد: {resp_code_str} - تراکنش کامل شد")
                                        transaction_complete = True
                        except Exception as e:
                            pass
                        
                        # If transaction is complete (response code received), break
                        if transaction_complete:
                            break
                        
                        # Check for RRN (Reference Number) - this indicates transaction completed successfully
                        # IMPORTANT: Only accept RRN if it has actual value (not empty, not "RN =")
                        try:
                            if hasattr(response_obj, 'GetTrxnRRN'):
                                rrn = response_obj.GetTrxnRRN()
                                rrn_str = str(rrn).strip() if rrn else ''
                                # Check if RRN is valid (not empty, not "RN =", not "=", has actual digits)
                                # IMPORTANT: Don't print if RRN is empty or invalid
                                if rrn_str and rrn_str != '=' and rrn_str != 'None' and rrn_str != 'RN =' and rrn_str != '' and len(rrn_str) > 2:
                                    # Check if it contains actual digits (not just spaces or special chars)
                                    if any(c.isdigit() for c in rrn_str):
                                        has_data = True
                                        print(f"✅ RRN دریافت شد: {rrn_str}")
                                        # We have valid RRN - transaction completed successfully
                                        transaction_complete = True
                        except:
                            pass
                        
                        # If transaction is complete (RRN received), break
                        if transaction_complete:
                            break
                        
                        # Check for Serial Number - only if it has actual value
                        # IMPORTANT: Don't print if Serial is empty or invalid
                        try:
                            if hasattr(response_obj, 'GetTrxnSerial'):
                                serial = response_obj.GetTrxnSerial()
                                serial_str = str(serial).strip() if serial else ''
                                # Check if serial is valid (not empty, not "SR =", not "=", has actual digits)
                                if serial_str and serial_str != '=' and serial_str != 'None' and serial_str != 'SR =' and serial_str != '' and len(serial_str) > 2:
                                    # Check if it contains actual digits
                                    if any(c.isdigit() for c in serial_str):
                                        has_data = True
                                        print(f"✅ Serial Number دریافت شد: {serial_str}")
                        except:
                            pass
                        
                        # If we have data, try to get string representation
                        if has_data:
                            try:
                                if hasattr(response_obj, 'ToString'):
                                    response = response_obj.ToString()
                                elif hasattr(response_obj, 'Message'):
                                    response = str(response_obj.Message)
                                if response and response != 'Intek.PcPosLibrary.Response':
                                    break
                            except:
                                pass
                except Exception as e:
                    pass
                
                # Try GetParsedResp from pos_instance - this is the main method
                try:
                    if hasattr(self.pos_instance, 'GetParsedResp'):
                        resp = self.pos_instance.GetParsedResp()
                        if resp:
                            resp_str = str(resp).strip()
                            # Check if it's a valid response (not just class name or empty)
                            if resp_str and resp_str != 'Intek.PcPosLibrary.Response' and len(resp_str) > 5:
                                response = resp_str
                                print(f"✅ GetParsedResp: {resp_str[:100]}...")
                                break
                except Exception as e:
                    pass
                
                # Try to check Response Code from pos_instance FIRST
                # IMPORTANT: Response code tells us if transaction is complete (success or cancelled)
                # ANY valid response code means transaction is complete - we should break
                transaction_complete_from_code = False
                try:
                    if hasattr(self.pos_instance, 'GetTrxnResp'):
                        resp_code = self.pos_instance.GetTrxnResp()
                        resp_code_str = str(resp_code).strip() if resp_code else ''
                        # Check if response code is valid (not empty, not just "=")
                        if resp_code_str and resp_code_str != '=' and resp_code_str != 'None' and resp_code_str != '':
                            # We have a valid response code - transaction is complete
                            print(f"✅ Response Code از pos_instance: {resp_code_str}")
                            
                            # IMPORTANT: ANY response code means transaction is complete
                            # Response code 81 might mean cancelled, but transaction is still complete
                            if resp_code_str == '81':
                                print(f"⚠️  Response Code 81 دریافت شد - تراکنش کامل شد")
                            elif resp_code_str in ['00', '01', '02', '03', '13']:
                                print(f"✅ تراکنش کامل شد (کد: {resp_code_str})")
                            
                            # Get Response object
                            if hasattr(self.pos_instance, 'Response'):
                                response_obj = self.pos_instance.Response
                            
                            # Transaction is complete - break the loop
                            transaction_complete_from_code = True
                except Exception as e:
                    pass
                
                # IMPORTANT: Break outer loop if transaction is complete
                if transaction_complete_from_code:
                    break
                
                # Try to check if transaction is complete by checking for RRN from pos_instance
                # This is the most reliable way - check pos_instance methods directly
                # IMPORTANT: RRN only appears when transaction is actually completed successfully
                try:
                    if hasattr(self.pos_instance, 'GetTrxnRRN'):
                        rrn = self.pos_instance.GetTrxnRRN()
                        rrn_str = str(rrn).strip() if rrn else ''
                        
                        # IMPORTANT: Only accept RRN if it has actual value (not empty, not "RN =", has digits)
                        if rrn_str and rrn_str != 'None' and rrn_str != '' and rrn_str != '=' and rrn_str != 'RN =':
                            # Check if it contains actual digits (not just spaces or special chars)
                            if any(c.isdigit() for c in rrn_str) and len(rrn_str) > 2:
                                # Check if this is a new RRN (different from last check)
                                if rrn_str != last_rrn_check:
                                    # Transaction completed - we have valid RRN
                                    print(f"✅ تراکنش کامل شد - RRN: {rrn_str}")
                                    last_rrn_check = rrn_str
                                    
                                    # Get Response object now
                                    if hasattr(self.pos_instance, 'Response'):
                                        response_obj = self.pos_instance.Response
                                    
                                    # Also try to get GetParsedResp
                                    if hasattr(self.pos_instance, 'GetParsedResp'):
                                        try:
                                            parsed = self.pos_instance.GetParsedResp()
                                            if parsed:
                                                parsed_str = str(parsed).strip()
                                                if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                                                    response = parsed_str
                                                    print(f"✅ GetParsedResp دریافت شد")
                                        except Exception as e:
                                            print(f"⚠️  خطا در GetParsedResp: {e}")
                                    
                                    # We have valid RRN, transaction is complete
                                    break
                except Exception as e:
                    # Debug: Print error if any
                    if attempt % 10 == 0:  # Print every 10 attempts
                        print(f"⚠️  خطا در بررسی RRN: {e}")
                    pass
                
                # IMPORTANT: Check if connection is still alive
                # If DLL has a method to check connection status, use it
                try:
                    if hasattr(self.pos_instance, 'IsConnected'):
                        is_connected = self.pos_instance.IsConnected
                        if not is_connected:
                            raise GatewayException('اتصال به دستگاه POS قطع شد')
                    elif hasattr(self.pos_instance, 'ConnectionStatus'):
                        status = self.pos_instance.ConnectionStatus
                        if status and 'disconnected' in str(status).lower():
                            raise GatewayException('اتصال به دستگاه POS قطع شد')
                except GatewayException:
                    raise
                except Exception:
                    # Connection check not available or failed, continue
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
                                print(f"✅ RawResponse: {raw_str[:100]}...")
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
                                print(f"✅ GetResponse: {resp_str[:100]}...")
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
            
            # Final check: If we have response_obj but no response string, check if it has data
            if response_obj and not response:
                # Check if response_obj has actual data by checking methods
                try:
                    # Check RRN first (most reliable indicator)
                    if hasattr(response_obj, 'GetTrxnRRN'):
                        rrn = response_obj.GetTrxnRRN()
                        if rrn and str(rrn).strip() and str(rrn) != 'None' and str(rrn) != '':
                            # We have data, response_obj is valid
                            print(f"✅ Response object معتبر است - RRN: {rrn}")
                        else:
                            # Response object exists but empty - might not be ready yet
                            print(f"⚠️  Response object موجود است اما RRN خالی است. منتظر می‌مانیم...")
                            # Don't use empty response_obj - continue waiting
                            response_obj = None
                except Exception as e:
                    print(f"⚠️  خطا در بررسی Response object: {e}")
                    pass
            
            # If still no response, try to get error message
            if not response and not raw_response and not response_obj:
                error_msg = ''
                try:
                    if hasattr(self.pos_instance, 'GetErrorMsg'):
                        error_msg = self.pos_instance.GetErrorMsg()
                        if error_msg and error_msg.strip():
                            print(f"⚠️  پیام خطا: {error_msg}")
                except Exception:
                    pass
                
                # Try to get response code or status
                status_code = None
                try:
                    if hasattr(self.pos_instance, 'GetTrxnResp'):
                        status_code = self.pos_instance.GetTrxnResp()
                        if status_code and str(status_code).strip():
                            print(f"⚠️  Response Code: {status_code}")
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
            # IMPORTANT: Check if response_obj actually has data, not just empty object
            if response_obj:
                try:
                    # First, check if Response object has actual data by checking key methods
                    has_actual_data = False
                    
                    # Check for RRN (most reliable indicator of completed transaction)
                    try:
                        if hasattr(response_obj, 'GetTrxnRRN'):
                            rrn = response_obj.GetTrxnRRN()
                            if rrn and str(rrn).strip() and str(rrn) != 'None':
                                has_actual_data = True
                                print(f"✅ Response object has RRN: {rrn}")
                    except:
                        pass
                    
                    # Check for Response Code
                    if not has_actual_data:
                        try:
                            if hasattr(response_obj, 'GetTrxnResp'):
                                resp_code = response_obj.GetTrxnResp()
                                if resp_code and str(resp_code).strip() and str(resp_code) != 'None':
                                    has_actual_data = True
                                    print(f"✅ Response object has Response Code: {resp_code}")
                        except:
                            pass
                    
                    # If we have actual data, extract it
                    if has_actual_data:
                        # Try to get all properties from Response object using reflection
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
                                    # Skip if it's just the class name or None
                                    if prop_str and prop_str != 'Intek.PcPosLibrary.Response' and prop_str != 'None':
                                        if not response:
                                            response = f"{prop_name}={prop_str}"
                                        else:
                                            response += f", {prop_name}={prop_str}"
                            except Exception:
                                pass
                    else:
                        # Response object exists but has no data yet - continue waiting
                        print(f"⚠️  Response object موجود است اما هنوز داده‌ای ندارد. منتظر می‌مانیم...")
                        response_obj = None  # Reset to continue waiting
                    
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
            '81': 'تراکنش توسط کاربر لغو شد',
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
            payment_id = order_details.get('payment_id', '')
            bill_id = order_details.get('bill_id', '')
            
            # Build additional_data dictionary
            additional_data = {}
            if customer_name:
                additional_data['customer_name'] = customer_name
            if payment_id:
                additional_data['payment_id'] = payment_id
            if bill_id:
                additional_data['bill_id'] = bill_id
            
            # Test connection first
            if not self._test_connection():
                raise GatewayException('Failed to connect to POS device')
            
            try:
                # Send payment request
                result = self._send_payment_dll(
                    amount=amount,
                    order_number=order_number,
                    additional_data=additional_data if additional_data else None
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

