import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message, Room
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"✅ User connected to room {self.room_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"🔌 User disconnected from room {self.room_id}")

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']
            username = data['username']
            room_id = self.room_id

            logger.info(f"📩 Received message from {username}: {message}")

            # Get user and room
            user = await sync_to_async(User.objects.get)(username=username)
            room = await sync_to_async(Room.objects.get)(id=room_id)
            
            # Create message
            new_message = await sync_to_async(Message.objects.create)(
                user=user,
                room=room,
                body=message
            )

            logger.info(f"💾 Message saved with ID: {new_message.id}")

            # Send to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'created': new_message.created.isoformat(),
                    'message_id': new_message.id,
                    'user_id': user.id,
                }
            )

        except User.DoesNotExist:
            logger.error(f"❌ User {username} does not exist")
            await self.send(text_data=json.dumps({
                'error': 'User not found'
            }))
        except Room.DoesNotExist:
            logger.error(f"❌ Room {room_id} does not exist")
            await self.send(text_data=json.dumps({
                'error': 'Room not found'
            }))
        except Exception as e:
            logger.error(f"❌ Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to send message'
            }))

    # Receive message from room group
    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps({
                'message': event['message'],
                'username': event['username'],
                'created': event['created'],
                'message_id': event['message_id'],
                'user_id': event['user_id'],
            }))
            logger.info(f"📤 Sent message {event['message_id']} to client")
        except Exception as e:
            logger.error(f"❌ Error sending to client: {str(e)}")