from django.contrib import admin
from django.urls import path, include
from apps.core.api import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/kiosk/', include('apps.core.urls')),
    path('health/', health.health_check, name='health'),
    path('health/ready/', health.readiness_check, name='readiness'),
    path('health/live/', health.liveness_check, name='liveness'),
]
