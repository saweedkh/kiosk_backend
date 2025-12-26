import logging
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger('kiosk')


class LogService:
    @staticmethod
    def _format_message(log_type, action, **kwargs):
        message_parts = [f"[{log_type.upper()}] {action}"]
        
        if kwargs.get('user'):
            message_parts.append(f"User: {kwargs['user']}")
        
        if kwargs.get('session_key'):
            message_parts.append(f"Session: {kwargs['session_key'][:8]}...")
        
        if kwargs.get('details'):
            import json
            details_str = json.dumps(kwargs['details'], ensure_ascii=False)
            message_parts.append(f"Details: {details_str}")
        
        if kwargs.get('ip_address'):
            message_parts.append(f"IP: {kwargs['ip_address']}")
        
        return " | ".join(message_parts)
    
    @staticmethod
    def create_system_log(
        log_type,
        action,
        level='info',
        user=None,
        session_key=None,
        details=None,
        ip_address=None,
        user_agent=None
    ):
        message = LogService._format_message(
            log_type=log_type,
            action=action,
            user=user,
            session_key=session_key,
            details=details,
            ip_address=ip_address
        )
        
        getattr(logger, level)(message)
    
    @staticmethod
    def log_info(log_type, action, **kwargs):
        LogService.create_system_log(
            log_type=log_type,
            action=action,
            level='info',
            **kwargs
        )
    
    @staticmethod
    def log_warning(log_type, action, **kwargs):
        LogService.create_system_log(
            log_type=log_type,
            action=action,
            level='warning',
            **kwargs
        )
    
    @staticmethod
    def log_error(log_type, action, **kwargs):
        LogService.create_system_log(
            log_type=log_type,
            action=action,
            level='error',
            **kwargs
        )
    
    @staticmethod
    def log_critical(log_type, action, **kwargs):
        LogService.create_system_log(
            log_type=log_type,
            action=action,
            level='critical',
            **kwargs
        )
    
    @staticmethod
    def create_transaction_log(
        transaction=None,
        transaction_ref=None,
        log_type=None,
        message=None,
        request_data=None,
        response_data=None,
        error_details=None
    ):
        transaction_id = transaction_ref or (transaction.transaction_id if transaction else 'N/A')
        
        log_message = f"[TRANSACTION] {log_type} | Transaction: {transaction_id} | {message}"
        
        if request_data:
            import json
            log_message += f" | Request: {json.dumps(request_data, ensure_ascii=False)}"
        
        if response_data:
            import json
            log_message += f" | Response: {json.dumps(response_data, ensure_ascii=False)}"
        
        if error_details:
            import json
            log_message += f" | Error: {json.dumps(error_details, ensure_ascii=False)}"
        
        logger.info(log_message)
