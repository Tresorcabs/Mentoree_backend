import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import get_user
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import Conversation, Message, UserStatus

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        # Extract token from query parameters
        query_string = scope.get('query_string', b'').decode('utf-8')
        token = None

        if query_string:
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token')

        if token:
            try:
                # Decode JWT token
                access_token = AccessToken(token)
                user_id = access_token.payload.get('user_id')

                if user_id:
                    # Get user from database
                    try:
                        user = await self.get_user_from_id(user_id)
                        scope['user'] = user
                    except User.DoesNotExist:
                        scope['user'] = AnonymousUser()
                else:
                    scope['user'] = AnonymousUser()
            except (InvalidToken, TokenError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_id(self, user_id):
        return User.objects.get(id=user_id)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']

        # Check if user has access to this conversation
        if not await self.check_conversation_access():
            await self.close()
            return

        # Join conversation room
        self.room_group_name = f'chat_{self.conversation_id}'

        # Add to room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Set user online
        await self.set_user_online()

        await self.accept()

        # Send conversation history
        await self.send_conversation_history()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Set user offline
        await self.set_user_offline()

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing_start':
                await self.handle_typing_start()
            elif message_type == 'typing_stop':
                await self.handle_typing_stop()
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)

        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')

    async def handle_chat_message(self, data):
        """Handle incoming chat message"""
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')

        if not content and message_type == 'text':
            await self.send_error('Message content cannot be empty')
            return

        # Save message to database
        message = await self.save_message(content, message_type)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': {
                        'id': message.sender.id,
                        'username': message.sender.username,
                        'first_name': message.sender.first_name,
                        'last_name': message.sender.last_name,
                        'profile_picture': message.sender.profile_picture,
                    },
                    'content': message.content,
                    'message_type': message.message_type,
                    'file': message.file.url if message.file else None,
                    'file_name': message.file_name,
                    'created_at': message.created_at.isoformat(),
                    'is_read': message.is_read,
                }
            }
        )

    async def handle_typing_start(self):
        """Handle typing indicator start"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_start',
                'user': {
                    'id': self.user.id,
                    'username': self.user.username,
                }
            }
        )

    async def handle_typing_stop(self):
        """Handle typing indicator stop"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_stop',
                'user': {
                    'id': self.user.id,
                    'username': self.user.username,
                }
            }
        )

    async def handle_mark_read(self, data):
        """Handle marking messages as read"""
        message_ids = data.get('message_ids', [])
        await self.mark_messages_read(message_ids)

    # Database operations
    @database_sync_to_async
    def check_conversation_access(self):
        """Check if user has access to the conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            # Check if user is either mentor or mentee in this conversation
            return (
                conversation.mentor.user == self.user or
                conversation.mentee.user == self.user
            )
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, message_type):
        """Save message to database"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            message_type=message_type,
        )
        # Update conversation timestamp
        conversation.save()
        return message

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read"""
        Message.objects.filter(
            id__in=message_ids,
            conversation_id=self.conversation_id
        ).exclude(sender=self.user).update(is_read=True, read_at=timezone.now())

    @database_sync_to_async
    def set_user_online(self):
        """Set user online status"""
        status, created = UserStatus.objects.get_or_create(user=self.user)
        status.set_online(room=self.room_group_name)

    @database_sync_to_async
    def set_user_offline(self):
        """Set user offline status"""
        try:
            status = UserStatus.objects.get(user=self.user)
            status.set_offline()
        except UserStatus.DoesNotExist:
            pass

    @database_sync_to_async
    def get_conversation_history(self):
        """Get conversation message history"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')

        message_data = []
        for message in messages:
            message_data.append({
                'id': message.id,
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'first_name': message.sender.first_name,
                    'last_name': message.sender.last_name,
                    'profile_picture': message.sender.profile_picture,
                },
                'content': message.content,
                'message_type': message.message_type,
                'file': message.file.url if message.file else None,
                'file_name': message.file_name,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read,
            })

        return message_data

    async def send_conversation_history(self):
        """Send conversation history to client"""
        history = await self.get_conversation_history()
        await self.send(text_data=json.dumps({
            'type': 'conversation_history',
            'messages': history
        }))

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # Event handlers for group messages
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps(event))

    async def typing_start(self, event):
        """Send typing start event to WebSocket"""
        await self.send(text_data=json.dumps(event))

    async def typing_stop(self, event):
        """Send typing stop event to WebSocket"""
        await self.send(text_data=json.dumps(event))


class StatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user status updates.
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']

        # Join status room
        await self.channel_layer.group_add(
            'user_status',
            self.channel_name
        )

        await self.accept()

        # Send current online users
        await self.send_online_users()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            'user_status',
            self.channel_name
        )

    @database_sync_to_async
    def get_online_users(self):
        """Get list of online users"""
        online_users = UserStatus.objects.filter(is_online=True).select_related('user')
        return [{
            'id': status.user.id,
            'username': status.user.username,
            'first_name': status.user.first_name,
            'last_name': status.user.last_name,
            'profile_picture': status.user.profile_picture,
            'last_seen': status.last_seen.isoformat(),
            'current_room': status.current_room,
        } for status in online_users]

    async def send_online_users(self):
        """Send list of online users to client"""
        online_users = await self.get_online_users()
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': online_users
        }))

    # Event handlers
    async def user_online(self, event):
        """Send user online event"""
        await self.send(text_data=json.dumps(event))

    async def user_offline(self, event):
        """Send user offline event"""
        await self.send(text_data=json.dumps(event))