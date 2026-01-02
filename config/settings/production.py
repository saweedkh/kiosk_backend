from .base import *
import os

# برای محیط لوکال بدون اینترنت
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS - برای لوکال می‌تواند localhost و IP محلی باشد
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,kiosk.local').split(',') if os.getenv('ALLOWED_HOSTS') else ['localhost', '127.0.0.1', 'kiosk.local']

# Security settings - برای لوکال بدون اینترنت SSL نیاز نیست
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - برای لوکال همه چیز مجاز است
CORS_ALLOWED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://kiosk.local',
]
CORS_ALLOW_ALL_ORIGINS = True  # برای لوکال
CORS_ALLOW_CREDENTIALS = True

# Static files (از base.py استفاده می‌کند)
# در production، باید collectstatic اجرا شود

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'kiosk.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'kiosk': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

