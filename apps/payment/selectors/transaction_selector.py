from apps.payment.models import Transaction


class TransactionSelector:
    @staticmethod
    def get_transaction_by_id(transaction_id):
        return Transaction.objects.filter(id=transaction_id).first()
    
    @staticmethod
    def get_transaction_by_transaction_id(transaction_id):
        return Transaction.objects.filter(transaction_id=transaction_id).first()
    
    @staticmethod
    def get_transactions_by_order(order_id):
        return Transaction.objects.filter(order_id=order_id).order_by('-created_at')
    
    @staticmethod
    def get_pending_transactions():
        return Transaction.objects.filter(status='pending').order_by('-created_at')
    
    @staticmethod
    def get_successful_transactions():
        return Transaction.objects.filter(status='success').order_by('-created_at')
    
    @staticmethod
    def get_failed_transactions():
        return Transaction.objects.filter(status='failed').order_by('-created_at')
    
    @staticmethod
    def get_transactions_by_status(status):
        return Transaction.objects.filter(status=status).order_by('-created_at')
    
    @staticmethod
    def get_transactions_by_gateway(gateway_name):
        return Transaction.objects.filter(gateway_name=gateway_name).order_by('-created_at')

