from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.core.api import health

urlpatterns = [
    # Django Admin (با prefix متفاوت برای جلوگیری از conflict با frontend)
    path('django-admin/', admin.site.urls),
    
    # API Routes
    path('api/kiosk/', include('apps.core.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health checks
    path('health/', health.health_check, name='health'),
    path('health/ready/', health.readiness_check, name='readiness'),
    path('health/live/', health.liveness_check, name='liveness'),
    
    # Next.js Static Files (_next/static)
    # در حالت EXE از FRONTEND_STATIC_PATH استفاده می‌کنیم
    re_path(
        r'^_next/static/(?P<path>.*)$',
        serve,
        {'document_root': getattr(settings, 'FRONTEND_STATIC_PATH', settings.STATIC_ROOT / 'frontend') / '_next' / 'static'}
    ),
    
    # Next.js Static Files (other assets)
    re_path(
        r'^static/(?P<path>.*)$',
        serve,
        {'document_root': getattr(settings, 'FRONTEND_STATIC_PATH', settings.STATIC_ROOT / 'frontend')}
    ),
    
    # Media files
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT}
    ),
]

# Serve Next.js admin pages (SPA routing)
# برای admin/login از فایل مخصوص استفاده کن، برای بقیه admin routes از admin/index.html
urlpatterns += [
    re_path(r'^admin/login/?$', 
            TemplateView.as_view(template_name='admin/login/index.html')),
    re_path(r'^admin/.*$', 
            TemplateView.as_view(template_name='admin/index.html')),
]

# Serve Next.js index.html for all other routes (SPA routing)
# این باید آخرین route باشد
urlpatterns += [
    re_path(r'^(?!django-admin|api|health|_next|static|media|admin).*$', 
            TemplateView.as_view(template_name='index.html')),
]

# در development، static files را serve کن
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
