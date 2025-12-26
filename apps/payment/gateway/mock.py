import uuid
from typing import Dict, Any
from django.utils import timezone
from .base import BasePaymentGateway
from .exceptions import GatewayException


class MockPaymentGateway(BasePaymentGateway):
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mock_transactions = {}
    
    def initiate_payment(self, amount: int, order_details: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        transaction_id = f"MOCK-{uuid.uuid4().hex[:16].upper()}"
        
        self.mock_transactions[transaction_id] = {
            'transaction_id': transaction_id,
            'amount': amount,
            'order_details': order_details,
            'status': 'pending',
            'created_at': timezone.now().isoformat(),
        }
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'redirect_url': f'/payment/mock/{transaction_id}',
            'gateway_response': {
                'status': 'pending',
                'message': 'Payment initiated successfully'
            }
        }
    
    def verify_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        if transaction_id not in self.mock_transactions:
            raise GatewayException('Transaction not found')
        
        transaction = self.mock_transactions[transaction_id]
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': transaction['status'],
            'amount': transaction['amount'],
            'gateway_response': {
                'status': transaction['status'],
                'verified_at': timezone.now().isoformat()
            }
        }
    
    def get_payment_status(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        if transaction_id not in self.mock_transactions:
            raise GatewayException('Transaction not found')
        
        transaction = self.mock_transactions[transaction_id]
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': transaction['status'],
            'amount': transaction['amount'],
            'gateway_response': {
                'status': transaction['status'],
                'checked_at': timezone.now().isoformat()
            }
        }
    
    def cancel_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        if transaction_id not in self.mock_transactions:
            raise GatewayException('Transaction not found')
        
        transaction = self.mock_transactions[transaction_id]
        transaction['status'] = 'cancelled'
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': 'cancelled',
            'gateway_response': {
                'status': 'cancelled',
                'cancelled_at': timezone.now().isoformat()
            }
        }
    
    def handle_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        transaction_id = request_data.get('transaction_id')
        status = request_data.get('status', 'success')
        
        if transaction_id and transaction_id in self.mock_transactions:
            self.mock_transactions[transaction_id]['status'] = status
        
        return {
            'success': True,
            'message': 'Webhook processed successfully'
        }
    
    def simulate_payment_success(self, transaction_id: str):
        if transaction_id in self.mock_transactions:
            self.mock_transactions[transaction_id]['status'] = 'success'
    
    def simulate_payment_failure(self, transaction_id: str):
        if transaction_id in self.mock_transactions:
            self.mock_transactions[transaction_id]['status'] = 'failed'

