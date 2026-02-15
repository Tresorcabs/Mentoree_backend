from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Case, When, BooleanField
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Conversation, Message, Task, UserStatus
from .serializers import (
    ConversationSerializer, MessageSerializer, TaskSerializer,
    TaskCreateSerializer, TaskUpdateSerializer, UserStatusSerializer
)
from profiles.models import MentorProfile, MenteeProfile
from users.models import CustomUser


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for conversations"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == 'mentor':
            mentor_profile = get_object_or_404(MentorProfile, user=user)
            return Conversation.objects.filter(mentor=mentor_profile)
        else:
            mentee_profile = get_object_or_404(MenteeProfile, user=user)
            return Conversation.objects.filter(mentee=mentee_profile)

    def create(self, request, *args, **kwargs):
        """Create a conversation between current user and specified other user"""
        other_user_id = request.data.get('other_user_id')
        if not other_user_id:
            return Response(
                {"other_user_id": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            other_user_id = int(other_user_id)
        except (ValueError, TypeError):
            return Response(
                {"other_user_id": "Invalid user ID format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        other_user = get_object_or_404(CustomUser, id=other_user_id)
        current_user = request.user

        # Determine mentor and mentee based on roles
        if current_user.role == 'mentor':
            mentor_profile = get_object_or_404(MentorProfile, user=current_user)
            if other_user.role == 'mentee':
                mentee_profile = get_object_or_404(MenteeProfile, user=other_user)
            else:
                return Response(
                    {"other_user_id": "Mentors can only create conversations with mentees."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif current_user.role == 'mentee':
            mentee_profile = get_object_or_404(MenteeProfile, user=current_user)
            if other_user.role == 'mentor':
                mentor_profile = get_object_or_404(MentorProfile, user=other_user)
            else:
                return Response(
                    {"other_user_id": "Mentees can only create conversations with mentors."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"detail": "Invalid user role."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            mentor=mentor_profile,
            mentee=mentee_profile
        ).first()

        if existing_conversation:
            # Return existing conversation
            serializer = self.get_serializer(existing_conversation)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Create new conversation
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(mentor=mentor_profile, mentee=mentee_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for a specific conversation"""
        conversation = self.get_object()

        # Mark messages as read for the current user
        conversation.messages.exclude(
            sender=request.user
        ).filter(is_read=False).update(is_read=True, read_at=timezone.now())

        messages = conversation.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a conversation"""
        conversation = self.get_object()
        content = request.data.get('content', '').strip()
        message_type = request.data.get('message_type', 'text')
        file = request.FILES.get('file')

        if not content and message_type == 'text' and not file:
            return Response(
                {'error': 'Message content or file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            message_type=message_type,
            file=file,
            file_name=file.name if file else None
        )

        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for tasks"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        conversation_id = self.request.query_params.get('conversation')

        if conversation_id:
            # Filter tasks by conversation
            conversation = get_object_or_404(Conversation, id=conversation_id)
            # Check if user has access to this conversation
            if not self._user_has_conversation_access(conversation):
                return Task.objects.none()
            return conversation.tasks.all()

        # Return all tasks for user's conversations
        if user.role == 'mentor':
            mentor_profile = get_object_or_404(MentorProfile, user=user)
            return Task.objects.filter(conversation__mentor=mentor_profile)
        else:
            mentee_profile = get_object_or_404(MenteeProfile, user=user)
            return Task.objects.filter(conversation__mentee=mentee_profile)

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'create':
            conversation_id = self.request.data.get('conversation_id')
            if conversation_id:
                conversation = get_object_or_404(Conversation, id=conversation_id)
                context['conversation'] = conversation
        return context

    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation_id')
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # Check if user can create tasks in this conversation
        if not self._user_can_create_tasks(conversation):
            raise PermissionError("You don't have permission to create tasks in this conversation")

        serializer.save(conversation=conversation)

    def _user_has_conversation_access(self, conversation):
        """Check if user has access to the conversation"""
        user = self.request.user
        if user.role == 'mentor':
            mentor_profile = get_object_or_404(MentorProfile, user=user)
            return conversation.mentor == mentor_profile
        else:
            mentee_profile = get_object_or_404(MenteeProfile, user=user)
            return conversation.mentee == mentee_profile

    def _user_can_create_tasks(self, conversation):
        """Check if user can create tasks in this conversation"""
        user = self.request.user
        # Only mentors can create tasks
        return user.role == 'mentor' and conversation.mentor.user == user


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_status_list(request):
    """Get status of all users"""
    user_statuses = UserStatus.objects.select_related('user').all()
    serializer = UserStatusSerializer(user_statuses, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_status_detail(request):
    """Get or update current user's status"""
    user_status, created = UserStatus.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = UserStatusSerializer(user_status)
        return Response(serializer.data)
    else:
        # Update status
        is_online = request.data.get('is_online')
        if is_online is not None:
            if is_online:
                user_status.set_online()
            else:
                user_status.set_offline()

        serializer = UserStatusSerializer(user_status)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_messages_count(request):
    """Get total unread messages count for current user"""
    user = request.user

    if user.role == 'mentor':
        mentor_profile = get_object_or_404(MentorProfile, user=user)
        conversations = Conversation.objects.filter(mentor=mentor_profile)
    else:
        mentee_profile = get_object_or_404(MenteeProfile, user=user)
        conversations = Conversation.objects.filter(mentee=mentee_profile)

    total_unread = 0
    for conversation in conversations:
        total_unread += conversation.messages.exclude(
            sender=user
        ).filter(is_read=False).count()

    return Response({'unread_count': total_unread})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request, conversation_id):
    """Mark messages as read in a conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Check access
    user = request.user
    if not ((user.role == 'mentor' and conversation.mentor.user == user) or
            (user.role == 'mentee' and conversation.mentee.user == user)):
        return Response(
            {'error': 'Access denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    message_ids = request.data.get('message_ids', [])
    if message_ids:
        Message.objects.filter(
            id__in=message_ids,
            conversation=conversation
        ).exclude(sender=user).update(is_read=True, read_at=timezone.now())
    else:
        # Mark all unread messages as read
        conversation.messages.exclude(
            sender=user
        ).filter(is_read=False).update(is_read=True, read_at=timezone.now())

    return Response({'status': 'Messages marked as read'})
