from django.urls import path
from .views import (
    ConversationListView,
    MessageListView,
    SendMessageView,
    SuggestReplyView,
    AcquireLockView,
    ReleaseLockView,
    LockStatusView,
)

urlpatterns = [
    # Conversations
    path('conversations/',                          ConversationListView.as_view()),
    path('conversations/<int:pk>/messages/',        MessageListView.as_view()),
    path('conversations/<int:pk>/messages/send/',   SendMessageView.as_view()),
    path('conversations/<int:pk>/suggest-reply/',   SuggestReplyView.as_view()),

    # Locks
    path('conversations/<int:pk>/lock/',            AcquireLockView.as_view()),    # POST
    path('conversations/<int:pk>/lock/release/',    ReleaseLockView.as_view()),    # DELETE
    path('conversations/<int:pk>/lock/status/',     LockStatusView.as_view()),     # GET
]