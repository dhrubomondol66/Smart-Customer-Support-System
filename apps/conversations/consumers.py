# apps/conversations/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ConversationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['pk']
        self.room_group_name = f"conversation_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def new_message(self, event):
        await self.send(text_data=json.dumps(event['message'])) 