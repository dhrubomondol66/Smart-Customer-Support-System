from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView

urlpatterns = [
    path('login/', LoginView.as_view()),         # POST /api/auth/login/
    path('refresh/', TokenRefreshView.as_view()), # POST /api/auth/refresh/
]