from functools import wraps
from apps.logs.services.log_service import LogService


def log_action(action_name, log_type='admin_action'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                LogService.log_info(
                    log_type=log_type,
                    action=action_name,
                    details={'function': func.__name__}
                )
                return result
            except Exception as e:
                LogService.log_error(
                    log_type=log_type,
                    action=f'{action_name}_error',
                    details={
                        'function': func.__name__,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
                raise
        return wrapper
    return decorator

