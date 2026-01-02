import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-in-production')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'apps.products',
    'apps.orders',
    'apps.payment',
    'apps.logs',
    'apps.admin_panel',
    'apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.logs.middleware.request_logging.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {'timeout': 30},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'apps.core.api.renderers.CustomJSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.api.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'apps.core.api.exceptions.api_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8080',
]
CORS_ALLOW_CREDENTIALS = True

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'kiosk.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'kiosk': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Payment Gateway Configuration
PAYMENT_GATEWAY_CONFIG = {
    'gateway_name': os.getenv('PAYMENT_GATEWAY_NAME', 'mock'),
    'merchant_id': os.getenv('PAYMENT_GATEWAY_MERCHANT_ID', ''),
    'terminal_id': os.getenv('PAYMENT_GATEWAY_TERMINAL_ID', ''),
    'tcp_host': os.getenv('POS_TCP_HOST', '192.168.1.100'),
    'tcp_port': int(os.getenv('POS_TCP_PORT', '1362')),
    'timeout': int(os.getenv('POS_TIMEOUT', '30')),
    'dll_path': str(BASE_DIR / 'pna.pcpos.dll'),
    'mock_payment_delay': float(os.getenv('MOCK_PAYMENT_DELAY', '3')),
    'mock_payment_success': os.getenv('MOCK_PAYMENT_SUCCESS', 'True') == 'True',
}

# Printer Configuration
PRINTER_ENABLED = os.getenv('PRINTER_ENABLED', 'False') == 'True'
PRINTER_IP = os.getenv('PRINTER_IP', '192.168.1.100')
PRINTER_PORT = int(os.getenv('PRINTER_PORT', '9100'))
STORE_NAME = os.getenv('STORE_NAME', 'فروشگاه')

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Kiosk Backend API',
    'VERSION': '1.0.0',
    'SCHEMA_PATH_PREFIX': '/api/kiosk/',
}
