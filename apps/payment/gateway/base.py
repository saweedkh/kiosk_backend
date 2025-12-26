from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePaymentGateway(ABC):
    
    @abstractmethod
    def initiate_payment(self, amount: int, order_details: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def verify_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def cancel_payment(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def handle_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

