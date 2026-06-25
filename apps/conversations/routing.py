from django.urls import path
from .consumers import ConversationConsumer

websocket_urlpatterns = [
    path('ws/conversations/<int:pk>/', ConversationConsumer.as_asgi()),
]