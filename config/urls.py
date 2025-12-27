from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.core.api import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/kiosk/', include('apps.core.urls')),
    path('health/', health.health_check, name='health'),
    path('health/ready/', health.readiness_check, name='readiness'),
    path('health/live/', health.liveness_check, name='liveness'),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
