from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'service': 'kiosk_backend'
        }, status=200)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'service': 'kiosk_backend'
        }, status=503)


def readiness_check(request):
    checks = {
        'database': False,
        'service': True
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = True
    except Exception as e:
        logger.error(f"Readiness check failed - Database: {str(e)}")
    
    if all(checks.values()):
        return JsonResponse({
            'status': 'ready',
            'checks': checks,
            'service': 'kiosk_backend'
        }, status=200)
    else:
        return JsonResponse({
            'status': 'not_ready',
            'checks': checks,
            'service': 'kiosk_backend'
        }, status=503)


def liveness_check(request):
    return JsonResponse({
        'status': 'alive',
        'service': 'kiosk_backend'
    }, status=200)

