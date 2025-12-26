import json
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('kiosk.request')


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._log_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_log_start_time'):
            duration = time.time() - request._log_start_time
            
            if request.path.startswith('/api/'):
                log_data = {
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': f"{round(duration, 3)}s",
                }
                
                if request.user.is_authenticated:
                    log_data['user'] = str(request.user)
                
                if hasattr(request, 'session') and request.session.session_key:
                    log_data['session'] = request.session.session_key[:8] + '...'
                
                if request.method in ['POST', 'PUT', 'PATCH']:
                    try:
                        body = json.loads(request.body.decode('utf-8'))
                        log_data['body'] = body
                    except:
                        pass
                
                log_message = f"{request.method} {request.path} | Status: {response.status_code} | Duration: {log_data['duration']}"
                
                if log_data.get('user'):
                    log_message += f" | User: {log_data['user']}"
                
                if log_data.get('session'):
                    log_message += f" | Session: {log_data['session']}"
                
                if response.status_code >= 500:
                    logger.error(log_message)
                elif response.status_code >= 400:
                    logger.warning(log_message)
                else:
                    logger.info(log_message)
        
        return response
