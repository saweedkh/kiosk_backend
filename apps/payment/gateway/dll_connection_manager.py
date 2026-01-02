"""
DLL Connection Manager for POS gateway.
"""
import time
from typing import Dict, Any
from apps.logs.services.log_service import LogService
from .exceptions import GatewayException
from .dll_helpers import check_pythonnet_available, get_clr_module


class DLLConnectionManager:
    """Manages DLL connection and configuration."""
    
    def __init__(self, config: Dict[str, Any], dll_path: str):
        """
        Initialize connection manager.
        
        Args:
            config: Gateway configuration
            dll_path: Path to DLL file
        """
        self.config = config
        self.dll_path = dll_path
        self.pos_instance = None
    
    def load_dll(self):
        """
        Load .NET DLL file using pythonnet.
        
        Raises:
            GatewayException: If DLL cannot be loaded
        """
        if not check_pythonnet_available():
            raise GatewayException('pythonnet is not installed. Install it with: pip install pythonnet')
        
        clr_module = get_clr_module()
        if not clr_module:
            raise GatewayException('Failed to load pythonnet clr module')
        
        try:
            # Add reference to DLL
            clr_module.AddReference(self.dll_path)
            
            # Import PCPOS class from the correct namespace
            from Intek.PcPosLibrary import PCPOS
            
            # Create instance
            self.pos_instance = PCPOS()
            
            # Configure connection
            self._configure_connection()
            
        except (OSError, ImportError, RuntimeError, AttributeError) as e:
            LogService.log_error(
                'payment',
                'dll_load_error',
                details={'error': str(e), 'error_type': type(e).__name__, 'dll_path': self.dll_path}
            )
            raise GatewayException(f'Failed to load DLL: {str(e)}')
        except Exception as e:
            LogService.log_error(
                'payment',
                'dll_load_unexpected_error',
                details={'error': str(e), 'error_type': type(e).__name__, 'dll_path': self.dll_path}
            )
            raise GatewayException(f'Failed to load DLL: {str(e)}')
    
    def _configure_connection(self):
        """Configure POS instance connection settings."""
        connection_type = self.config.get('connection_type', 'tcp')
        
        # Always use TCP/IP (Socket) connection, not serial
        if connection_type == 'serial':
            import warnings
            warnings.warn('Serial connection requested but using TCP/IP instead. Set POS_CONNECTION_TYPE=tcp in .env')
            connection_type = 'tcp'
        
        # Configure TCP/IP (Socket) connection
        self.pos_instance.Ip = str(self.config.get('tcp_host', '192.168.1.100'))
        tcp_port = self.config.get('tcp_port', 1362)
        self.pos_instance.Port = int(tcp_port) if isinstance(tcp_port, str) else tcp_port
        self.pos_instance.ConnectionType = self.pos_instance.cnType.LAN
        
        # Configure timeout
        self._configure_timeout()
        
        # Configure keep-alive
        self._configure_keepalive()
        
        # Set terminal ID
        self._configure_terminal_id()
        
        # Set merchant ID
        self._configure_merchant_id()
        
        # Set serial number
        self._configure_serial_number()
    
    def _configure_timeout(self):
        """Configure timeout settings."""
        timeout_ms = 120000  # 120 seconds in milliseconds
        
        if hasattr(self.pos_instance, 'Timeout'):
            self.pos_instance.Timeout = timeout_ms
        elif hasattr(self.pos_instance, 'ConnectionTimeout'):
            self.pos_instance.ConnectionTimeout = timeout_ms
        elif hasattr(self.pos_instance, 'ReceiveTimeout'):
            self.pos_instance.ReceiveTimeout = timeout_ms
    
    def _configure_keepalive(self):
        """Configure keep-alive settings."""
        if hasattr(self.pos_instance, 'KeepAlive'):
            self.pos_instance.KeepAlive = True
        elif hasattr(self.pos_instance, 'KeepConnectionAlive'):
            self.pos_instance.KeepConnectionAlive = True
    
    def _configure_terminal_id(self):
        """Configure terminal ID."""
        terminal_id = self.config.get('terminal_id', '')
        if terminal_id:
            self.pos_instance.TerminalID = str(terminal_id)
    
    def _configure_merchant_id(self):
        """Configure merchant ID."""
        merchant_id = self.config.get('merchant_id', '')
        if merchant_id and hasattr(self.pos_instance, 'R0Merchant'):
            self.pos_instance.R0Merchant = str(merchant_id)
    
    def _configure_serial_number(self):
        """Configure device serial number."""
        serial_number = self.config.get('device_serial_number', '')
        if serial_number:
            if hasattr(self.pos_instance, 'SerialNumber'):
                self.pos_instance.SerialNumber = str(serial_number)
            elif hasattr(self.pos_instance, 'DeviceSerial'):
                self.pos_instance.DeviceSerial = str(serial_number)
    
    def test_connection(self) -> bool:
        """
        Test connection to POS device.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            GatewayException: If connection test fails
        """
        if not self.pos_instance:
            return False
        
        try:
            return self.pos_instance.TestConnection()
        except (AttributeError, RuntimeError) as e:
            LogService.log_error(
                'payment',
                'dll_connection_test_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
            raise GatewayException(f'Connection test failed: {str(e)}')
        except Exception as e:
            LogService.log_error(
                'payment',
                'dll_connection_test_unexpected_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
            raise GatewayException(f'Connection test failed: {str(e)}')
    
    def ensure_connection(self):
        """
        Ensure connection is established, reconnect if needed.
        
        Raises:
            GatewayException: If connection cannot be established
        """
        try:
            if hasattr(self.pos_instance, 'TestConnection'):
                connection_ok = self.pos_instance.TestConnection()
                if not connection_ok:
                    LogService.log_warning('payment', 'dll_initial_connection_failed', details={
                        'host': self.config.get('tcp_host'),
                        'port': self.config.get('tcp_port')
                    })
                    # Try to reconnect
                    time.sleep(1)
                    connection_ok = self.pos_instance.TestConnection()
                    if not connection_ok:
                        LogService.log_error('payment', 'dll_reconnection_failed')
                        raise GatewayException('اتصال به دستگاه POS برقرار نشد')
                
                LogService.log_info('payment', 'dll_connection_established', details={
                    'host': self.config.get('tcp_host'),
                    'port': self.config.get('tcp_port')
                })
        except GatewayException:
            raise
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_connection_test_warning',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        except Exception as e:
            LogService.log_warning(
                'payment',
                'dll_connection_test_unexpected_warning',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
    
    def configure_payment(self, amount: int, order_number: str, additional_data: Dict[str, Any] = None):
        """
        Configure payment parameters on POS instance.
        
        Args:
            amount: Payment amount in Rial
            order_number: Order number
            additional_data: Additional payment data
        """
        # Set amount
        self.pos_instance.Amount = str(amount)
        
        # Set order number
        if order_number and hasattr(self.pos_instance, 'OrderNumber'):
            self.pos_instance.OrderNumber = str(order_number)
        
        # Set additional data
        if additional_data:
            if additional_data.get('customer_name') and hasattr(self.pos_instance, 'CustomerName'):
                self.pos_instance.CustomerName = additional_data['customer_name']
            
            # Set Payment ID
            payment_id = additional_data.get('payment_id', '')
            if payment_id:
                for prop_name in ['PaymentID', 'PaymentId', 'PD']:
                    if hasattr(self.pos_instance, prop_name):
                        setattr(self.pos_instance, prop_name, str(payment_id))
                        break
            
            # Set Bill ID
            bill_id = additional_data.get('bill_id', '')
            if bill_id:
                for prop_name in ['BillID', 'BillId', 'BI']:
                    if hasattr(self.pos_instance, prop_name):
                        setattr(self.pos_instance, prop_name, str(bill_id))
                        break
    
    def cleanup(self):
        """Cleanup POS instance."""
        if self.pos_instance:
            try:
                if hasattr(self.pos_instance, 'Dispose'):
                    self.pos_instance.Dispose()
            except (AttributeError, RuntimeError) as e:
                LogService.log_warning(
                    'payment',
                    'dll_cleanup_dispose_error',
                    details={'error': str(e), 'error_type': type(e).__name__}
                )
            finally:
                self.pos_instance = None

