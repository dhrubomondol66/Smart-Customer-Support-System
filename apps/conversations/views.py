from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    MessageSerializer,
    SendMessageSerializer,
    SuggestReplySerializer,
    LockStatusSerializer,
)
from .services.lock_service import LockService
from .services.suggestion_engine import SuggestionEngine
from .tasks import analyze_sentiment


CONVERSATION_LIST_PARAMS = [
    openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description='Search by customer name',
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        'status',
        openapi.IN_QUERY,
        description='Filter by status',
        type=openapi.TYPE_STRING,
        enum=['open', 'closed', 'pending'],
    ),
    openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description='Page number',
        type=openapi.TYPE_INTEGER,
    ),
]


# ─────────────────────────────────────────────
# 4.1  Conversation List
# ─────────────────────────────────────────────
@method_decorator(
    name='get',
    decorator=swagger_auto_schema(manual_parameters=CONVERSATION_LIST_PARAMS),
)
class ConversationListView(generics.ListAPIView):
    serializer_class   = ConversationListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['status']           # ?status=open
    search_fields      = ['customer_name']    # ?search=John

    def get_queryset(self):
        return Conversation.objects.all()


# ─────────────────────────────────────────────
# 4.2  Thread History
# ─────────────────────────────────────────────
class MessageListView(generics.ListAPIView):
    serializer_class   = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = None

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return Message.objects.filter(
            conversation_id=self.kwargs['pk']
        ).order_by('timestamp')


# ─────────────────────────────────────────────
# 4.3  Agent Sends Reply
# ─────────────────────────────────────────────
class SendMessageView(APIView):
    serializer_class = SendMessageSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=SendMessageSerializer,
        responses={201: MessageSerializer}
    )
    def post(self, request, pk):
        # 1. Check conversation exists
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=404)

        # 2. Check lock — block if locked by someone else
        lock_owner = LockService.get_lock_owner(pk)
        if lock_owner and lock_owner != str(request.user.id):
            return Response(
                {
                    'error': 'Conversation is locked by another agent.',
                    'locked_by': lock_owner
                },
                status=status.HTTP_423_LOCKED
            )

        # 3. Validate input
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data['message']

        # 4. Save message immediately
        msg = Message.objects.create(
            conversation=conversation,
            sender='agent',
            agent=request.user,
            message=text
        )

        # 5. Fire Celery task — non-blocking
        analyze_sentiment.delay(conversation.id, text)

        # 6. Broadcast via WebSocket (if Channels configured)
        _broadcast_message(pk, {
            'id':        msg.id,
            'sender':    'agent',
            'message':   text,
            'timestamp': str(msg.timestamp),
        })

        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


def _broadcast_message(conversation_id: int, data: dict):
    """Push new message to WebSocket room. Silently skips if Channels not installed."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"conversation_{conversation_id}",
                {"type": "new_message", "message": data}
            )
    except Exception:
        pass  # Channels not configured — polling fallback is fine


# ─────────────────────────────────────────────
# 4.4  AI Suggestion
# ─────────────────────────────────────────────
class SuggestReplyView(APIView):
    serializer_class = SuggestReplySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=SuggestReplySerializer,
        responses={
            200: openapi.Response('AI Suggestion', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'suggestion': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def post(self, request, pk):
        serializer = SuggestReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message    = serializer.validated_data['message']
        suggestion = SuggestionEngine.get_suggestion(message)
        return Response({'suggestion': suggestion})


# ─────────────────────────────────────────────
# Lock Endpoints
# ─────────────────────────────────────────────
class AcquireLockView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Lock status response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'conversation_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )),
            423: openapi.Response('Lock occupied', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'locked_by': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ))
        }
    )
    def post(self, request, pk):
        acquired = LockService.acquire_lock(pk, request.user.id)
        if acquired:
            return Response({'status': 'lock acquired', 'conversation_id': pk})
        owner = LockService.get_lock_owner(pk)
        return Response(
            {'error': 'Already locked', 'locked_by': owner},
            status=status.HTTP_423_LOCKED
        )


class ReleaseLockView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Lock released successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )),
            403: openapi.Response('Not authorized to release lock', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ))
        }
    )
    def delete(self, request, pk):
        released = LockService.release_lock(pk, request.user.id)
        if released:
            return Response({'status': 'lock released'})
        return Response(
            {'error': 'You do not own this lock'},
            status=status.HTTP_403_FORBIDDEN
        )


class LockStatusView(APIView):
    serializer_class = LockStatusSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: LockStatusSerializer}
    )
    def get(self, request, pk):
        owner = LockService.get_lock_owner(pk)
        ttl   = LockService.calculate_ttl(pk)
        data  = {
            'conversation_id': pk,
            'locked':          owner is not None,
            'owner_agent_id':  owner,
            'ttl_seconds':     ttl,
        }
        return Response(LockStatusSerializer(data).data)