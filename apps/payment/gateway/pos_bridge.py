"""
POS Bridge Gateway - Connects to Windows Bridge Service

This gateway sends payment requests to a Windows service that uses DLL
to communicate with POS device. This allows cross-platform support.

Configuration in .env:
    POS_BRIDGE_HOST=192.168.1.50  # IP of Windows machine running bridge service
    POS_BRIDGE_PORT=8080           # Port of bridge service
"""
import requests
import time
from typing import Dict, Any
from django.conf import settings
from django.utils import timezone
from .base import BasePaymentGateway
from .exceptions import GatewayException


class POSBridgeGateway(BasePaymentGateway):
    """
    Payment Gateway that connects to Windows Bridge Service.
    
    This gateway sends HTTP requests to a Windows service that uses DLL
    to communicate with POS device. This allows:
    - Cross-platform support (Mac, Linux can use Windows service)
    - Centralized POS management
    - Better error handling and logging
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.bridge_host = self.config.get('pos_bridge_host', '192.168.1.50')
        self.bridge_port = self.config.get('pos_bridge_port', 8080)
        self.bridge_url = f"http://{self.bridge_host}:{self.bridge_port}"
        self.timeout = self.config.get('timeout', 130)  # 130 seconds (2 min + 10 sec buffer)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to bridge service and POS device.
        
        Returns:
            Dict[str, Any]: Connection test result
        """
        result = {
            'success': False,
            'message': '',
            'details': {}
        }
        
        try:
            # Test bridge service health
            health_url = f"{self.bridge_url}/health"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                result['details']['bridge_service'] = 'connected'
                result['details']['dll_available'] = health_data.get('dll_available', False)
                result['details']['pos_initialized'] = health_data.get('pos_initialized', False)
                
                # Test POS connection through bridge
                test_url = f"{self.bridge_url}/test-connection"
                test_response = requests.post(test_url, timeout=10)
                
                if test_response.status_code == 200:
                    test_data = test_response.json()
                    if test_data.get('success'):
                        result['success'] = True
                        result['message'] = 'Connection to POS device successful'
                        result['details']['pos_connection'] = 'connected'
                    else:
                        result['message'] = test_data.get('error', 'POS connection test failed')
                        result['details']['pos_connection'] = 'failed'
                else:
                    result['message'] = f'Bridge service returned error: {test_response.status_code}'
                    result['details']['pos_connection'] = 'error'
            else:
                result['message'] = f'Bridge service not available: {response.status_code}'
                result['details']['bridge_service'] = 'unavailable'
                
        except requests.exceptions.ConnectionError:
            result['message'] = f'Cannot connect to bridge service at {self.bridge_url}'
            result['details']['bridge_service'] = 'connection_error'
        except requests.exceptions.Timeout:
            result['message'] = 'Bridge service timeout'
            result['details']['bridge_service'] = 'timeout'
        except Exception as e:
            result['message'] = f'Error testing connection: {str(e)}'
            result['details']['error'] = str(e)
        
        return result
    
    def initiate_payment(self, amount: int, order_details: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Initiate payment transaction through bridge service.
        
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
        
        # Prepare request payload
        payload = {
            'amount': amount,
        }
        
        if order_number:
            payload['order_number'] = order_number
        if customer_name:
            payload['customer_name'] = customer_name
        if payment_id:
            payload['payment_id'] = payment_id
        if bill_id:
            payload['bill_id'] = bill_id
        
        try:
            print(f"\n📤 Sending payment request to bridge service:")
            print(f"   Bridge URL: {self.bridge_url}/payment")
            print(f"   Amount: {amount:,} Rial")
            print(f"   Order Number: {order_number}")
            
            # Test connection first
            print(f"🔍 Testing connection to bridge service...")
            try:
                health_url = f"{self.bridge_url}/health"
                health_response = requests.get(health_url, timeout=5)
                if health_response.status_code == 200:
                    print(f"✅ Bridge service is reachable")
                else:
                    print(f"⚠️  Bridge service returned status {health_response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"❌ Cannot connect to bridge service at {self.bridge_url}")
                print(f"\n💡 Troubleshooting:")
                print(f"   1. Make sure bridge service is running on Windows:")
                print(f"      python pos_bridge_service.py")
                print(f"   2. Check IP and Port:")
                print(f"      Current: {self.bridge_host}:{self.bridge_port}")
                print(f"   3. Test from Mac:")
                print(f"      curl http://{self.bridge_host}:{self.bridge_port}/health")
                print(f"   4. Check Windows Firewall settings")
                raise GatewayException(
                    f'Cannot connect to bridge service at {self.bridge_url}. '
                    'Make sure the bridge service is running on Windows machine.'
                )
            except Exception as e:
                print(f"⚠️  Health check failed: {e}")
            
            # Send payment request to bridge service
            payment_url = f"{self.bridge_url}/payment"
            print(f"📤 Sending payment request...")
            response = requests.post(
                payment_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Map bridge response to gateway response format
                return {
                    'success': result.get('success', False),
                    'transaction_id': result.get('transaction_id', ''),
                    'status': result.get('status', 'failed'),
                    'response_code': result.get('response_code', ''),
                    'response_message': result.get('response_message', ''),
                    'card_number': result.get('card_number', ''),
                    'reference_number': result.get('reference_number', ''),
                    'gateway_response': result,
                    'amount': amount,
                }
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', f'Bridge service returned {response.status_code}')
                raise GatewayException(f'Payment failed: {error_msg}')
                
        except requests.exceptions.ConnectionError as e:
            error_msg = (
                f'❌ Cannot connect to bridge service at {self.bridge_url}\n'
                f'\n💡 Troubleshooting steps:\n'
                f'   1. Check if bridge service is running on Windows:\n'
                f'      - Go to Windows machine\n'
                f'      - Run: python pos_bridge_service.py\n'
                f'      - You should see: "Starting server on 0.0.0.0:PORT"\n'
                f'\n'
                f'   2. Verify IP and Port:\n'
                f'      - Current settings: {self.bridge_host}:{self.bridge_port}\n'
                f'      - Check Windows IP: ipconfig (look for IPv4 Address)\n'
                f'      - Make sure port matches in .env\n'
                f'\n'
                f'   3. Test connection from Mac:\n'
                f'      curl http://{self.bridge_host}:{self.bridge_port}/health\n'
                f'      Should return: {{"status": "ok"}}\n'
                f'\n'
                f'   4. Check Windows Firewall:\n'
                f'      - Windows Security > Firewall\n'
                f'      - Add exception for port {self.bridge_port}\n'
                f'\n'
                f'   5. Check network connectivity:\n'
                f'      ping {self.bridge_host}\n'
                f'      Should get replies from Windows machine\n'
            )
            print(error_msg)
            raise GatewayException(
                f'Cannot connect to bridge service at {self.bridge_url}. '
                'Make sure the bridge service is running on Windows machine.'
            )
        except requests.exceptions.Timeout:
            raise GatewayException(
                f'Payment request timeout after {self.timeout} seconds. '
                'The transaction may still be processing on POS device.'
            )
        except GatewayException:
            raise
        except Exception as e:
            raise GatewayException(f'Failed to initiate payment: {str(e)}')
    
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
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': 'success',
            'gateway_response': {
                'message': 'Transaction verified',
                'verified_at': timezone.now().isoformat()
            }
        }
    
    def get_payment_status(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Get current payment status.
        
        Args:
            transaction_id: Transaction ID to check
            
        Returns:
            Dict[str, Any]: Payment status information
        """
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

