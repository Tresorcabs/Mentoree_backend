from rest_framework import serializers
from .models import Conversation, Message, Task, UserStatus
from users.models import CustomUser
from profiles.models import MentorProfile, MenteeProfile


class UserStatusSerializer(serializers.ModelSerializer):
    """Serializer for user status"""
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserStatus
        fields = ['user', 'is_online', 'last_seen', 'current_room']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'profile_picture': obj.user.profile_picture,
        }


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages"""
    sender = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'content', 'message_type', 'file', 'file_name',
            'created_at', 'is_read', 'read_at', 'is_mine'
        ]
        read_only_fields = ['id', 'created_at', 'is_read', 'read_at']

    def get_sender(self, obj):
        return {
            'id': obj.sender.id,
            'username': obj.sender.username,
            'first_name': obj.sender.first_name,
            'last_name': obj.sender.last_name,
            'profile_picture': obj.sender.profile_picture,
        }

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user
        return False


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversations"""
    mentor = serializers.SerializerMethodField()
    mentee = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'mentor', 'mentee', 'created_at', 'updated_at',
            'is_active', 'last_message', 'unread_count', 'other_user'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_mentor(self, obj):
        return {
            'id': obj.mentor.user.id,
            'username': obj.mentor.user.username,
            'first_name': obj.mentor.user.first_name,
            'last_name': obj.mentor.user.last_name,
            'profile_picture': obj.mentor.user.profile_picture,
        }

    def get_mentee(self, obj):
        return {
            'id': obj.mentee.user.id,
            'username': obj.mentee.user.username,
            'first_name': obj.mentee.user.first_name,
            'last_name': obj.mentee.user.last_name,
            'profile_picture': obj.mentee.user.profile_picture,
        }

    def get_last_message(self, obj):
        last_msg = obj.last_message
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.exclude(
                sender=request.user
            ).filter(is_read=False).count()
        return 0

    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if obj.mentor.user == request.user:
                return self.get_mentee(obj)
            else:
                return self.get_mentor(obj)
        return None


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for tasks"""
    assigned_by = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    can_update = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'assigned_by', 'assigned_to',
            'status', 'priority', 'due_date', 'created_at', 'updated_at',
            'proof_file', 'proof_description', 'completed_at', 'can_update'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']

    def get_assigned_by(self, obj):
        return {
            'id': obj.assigned_by.id,
            'username': obj.assigned_by.username,
            'first_name': obj.assigned_by.first_name,
            'last_name': obj.assigned_by.last_name,
            'profile_picture': obj.assigned_by.profile_picture,
        }

    def get_assigned_to(self, obj):
        return {
            'id': obj.assigned_to.id,
            'username': obj.assigned_to.username,
            'first_name': obj.assigned_to.first_name,
            'last_name': obj.assigned_to.last_name,
            'profile_picture': obj.assigned_to.profile_picture,
        }

    def get_can_update(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Mentor can update all tasks, mentee can only update their assigned tasks
            if request.user.role == 'mentor':
                return True
            elif request.user.role == 'mentee' and obj.assigned_to == request.user:
                return True
        return False


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date']

    def validate_assigned_to(self, value):
        """Validate that assigned_to user exists and is a mentee"""
        try:
            # Handle case where value is a user ID (integer)
            if isinstance(value, int):
                user_id = value
            # Handle case where value is a user object (dict with 'id' key)
            elif isinstance(value, dict) and 'id' in value:
                user_id = value['id']
            # Handle case where value is a user object (CustomUser instance)
            elif hasattr(value, 'id'):
                user_id = value.id
            else:
                raise serializers.ValidationError("Invalid assigned_to value format.")

            user = CustomUser.objects.get(id=user_id)
            if user.role != 'mentee':
                raise serializers.ValidationError("Tasks can only be assigned to mentees.")
            return user
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Assigned user does not exist.")

    def create(self, validated_data):
        request = self.context.get('request')
        conversation = self.context.get('conversation')

        # Set assigned_by to current user (should be mentor)
        validated_data['assigned_by'] = request.user

        # Remove conversation from validated_data to avoid duplication
        validated_data.pop('conversation', None)
        validated_data.pop('conversation_id', None)

        # Create task
        task = Task.objects.create(conversation=conversation, **validated_data)
        return task


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tasks"""

    class Meta:
        model = Task
        fields = ['status', 'proof_file', 'proof_description']

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Only allow status updates to 'completed' with proof for mentees
        if request.user.role == 'mentee':
            if 'status' in validated_data and validated_data['status'] == 'completed':
                if not validated_data.get('proof_file') and not validated_data.get('proof_description'):
                    raise serializers.ValidationError(
                        "Proof of completion (file or description) is required to mark task as completed."
                    )
                instance.mark_completed(
                    proof_file=validated_data.get('proof_file'),
                    proof_description=validated_data.get('proof_description')
                )
            else:
                raise serializers.ValidationError("Mentees can only mark tasks as completed with proof.")
        else:
            # Mentors can update status freely
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        return instance