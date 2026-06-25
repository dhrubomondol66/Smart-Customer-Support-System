from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ['id', 'sender', 'message', 'timestamp']


class ConversationListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model  = Conversation
        fields = ['id', 'customer_name', 'last_message', 'status', 'created_at']

    def get_last_message(self, obj):
        return obj.get_last_message()


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model  = Conversation
        fields = ['id', 'customer_name', 'status', 'sentiment', 'created_at', 'messages']


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class SuggestReplySerializer(serializers.Serializer):
    message = serializers.CharField()


class LockStatusSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    locked          = serializers.BooleanField()
    owner_agent_id  = serializers.CharField(allow_null=True)
    ttl_seconds     = serializers.IntegerField()