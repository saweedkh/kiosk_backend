import os
from pathlib import Path
from dotenv import load_dotenv

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
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'kiosk_db'),
        'USER': os.getenv('DATABASE_USER', 'kiosk_user'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fa'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

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
    "http://localhost:3000",
    "http://localhost:8080",
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
        'simple': {
            'format': '{levelname} {message}',
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
        'kiosk.request': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

PAYMENT_GATEWAY_CONFIG = {
    'gateway_name': os.getenv('PAYMENT_GATEWAY_NAME', 'mock'),
    'is_active': os.getenv('PAYMENT_GATEWAY_ACTIVE', 'True') == 'True',
    'api_key': os.getenv('PAYMENT_GATEWAY_API_KEY', ''),
    'api_secret': os.getenv('PAYMENT_GATEWAY_API_SECRET', ''),
    'merchant_id': os.getenv('PAYMENT_GATEWAY_MERCHANT_ID', ''),
    'terminal_id': os.getenv('PAYMENT_GATEWAY_TERMINAL_ID', ''),
    'callback_url': os.getenv('PAYMENT_GATEWAY_CALLBACK_URL', ''),
    # POS Card Reader Configuration
    'connection_type': os.getenv('POS_CONNECTION_TYPE', 'tcp'),  # 'serial' or 'tcp'
    'serial_port': os.getenv('POS_SERIAL_PORT', 'COM1'),  # e.g., 'COM1', '/dev/ttyUSB0'
    'serial_baudrate': int(os.getenv('POS_SERIAL_BAUDRATE', '9600')),
    'tcp_host': os.getenv('POS_TCP_HOST', '192.168.1.100'),
    'tcp_port': int(os.getenv('POS_TCP_PORT', '1362')),
    'timeout': int(os.getenv('POS_TIMEOUT', '30')),
    # DLL Configuration (if using DLL)
    'pos_use_dll': os.getenv('POS_USE_DLL', 'False') == 'True',
    'dll_path': os.getenv('POS_DLL_PATH', ''),  # Path to DLL file (e.g., 'C:/path/to/pna.pcpos.dll')
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Kiosk Backend API',
    'DESCRIPTION': 'API documentation for Kiosk Backend - Store management system with card reader payment integration',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/kiosk/',
    'TAGS': [
        {'name': 'Products', 'description': 'Product listing and details endpoints'},
        {'name': 'Categories', 'description': 'Category listing endpoints'},
        {'name': 'Orders', 'description': 'Order management endpoints'},
        {'name': 'Invoices', 'description': 'Invoice generation and download endpoints'},
        {'name': 'Payment', 'description': 'Payment processing endpoints'},
        {'name': 'Transactions', 'description': 'Payment transaction endpoints'},
        {'name': 'Admin - Auth', 'description': 'Admin authentication endpoints'},
        {'name': 'Admin - Products', 'description': 'Admin product management endpoints'},
        {'name': 'Admin - Categories', 'description': 'Admin category management endpoints'},
        {'name': 'Admin - Orders', 'description': 'Admin order management endpoints'},
        {'name': 'Admin - Reports', 'description': 'Admin reporting endpoints'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'SORT_OPERATIONS': True,
    'SORT_TAGS': True,
    'TAG_ORDER': [
        'Products',
        'Categories',
        'Orders',
        'Invoices',
        'Payment',
        'Transactions',
        'Admin - Auth',
        'Admin - Products',
        'Admin - Categories',
        'Admin - Orders',
        'Admin - Reports',
    ],
    'PREPEND_COMPONENTS': {
        'securitySchemes': {
            'jwtAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'JWT token authentication. Get token from /api/kiosk/admin/auth/login/'
            }
        }
    },
    'SECURITY': [{'jwtAuth': []}],
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

