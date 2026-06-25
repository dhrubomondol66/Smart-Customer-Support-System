"""
URL configuration for smart_customer_support project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def health_check(request):
    """Lightweight liveness probe used by Render's healthCheckPath."""
    return JsonResponse({"status": "ok"})


schema_view = get_schema_view(
    openapi.Info(
        title="Smart Customer Support Inbox API",
        default_version='v1',
        description="API documentation for Support Inbox Engine",
        contact=openapi.Contact(email="admin@test.com"),
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    # Health check — no auth required (Render liveness probe)
    path('api/health/', health_check, name='health-check'),

    # Admin
    path('admin/', admin.site.urls),

    # App APIs
    path('auth/', include('apps.accounts.urls')),
    path('', include('apps.conversations.urls')),

    # Swagger UI  → http://127.0.0.1:8000/swagger/
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),

    # Redoc UI   → http://127.0.0.1:8000/redoc/
    path('redoc/',   schema_view.with_ui('redoc',   cache_timeout=0)),

    # Raw JSON schema → http://127.0.0.1:8000/swagger.json
    path('swagger.json', schema_view.without_ui(cache_timeout=0)),
]