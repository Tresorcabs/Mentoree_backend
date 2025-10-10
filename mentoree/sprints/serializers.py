from rest_framework import serializers
from .models import Sprint, Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'due_date', 'status', 'created_at', 'updated_at']


class SprintSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    mentee = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Sprint
        fields = ['id', 'mentor', 'mentee', 'title', 'start_date', 'end_date', 'objectives', 'created_at', 'tasks']
        read_only_fields = ['mentor', 'created_at']


class SprintCreateSerializer(serializers.ModelSerializer):
    mentee_id = serializers.IntegerField(write_only=True, required=False)
    mentee = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Sprint
        fields = ['mentee_id', 'mentee', 'title', 'start_date', 'end_date', 'objectives']
        extra_kwargs = {
            'mentee_id': {'write_only': True},
            'mentee': {'write_only': True}
        }

    def validate(self, data):
        from users.models import CustomUser
        import logging
        logger = logging.getLogger(__name__)
        
        # Get mentee_id from either mentee or mentee_id field
        mentee_id = data.get('mentee') or data.get('mentee_id')
        if not mentee_id:
            raise serializers.ValidationError({"mentee_id": "This field is required."})
        
        # Debug: Log all users with role 'mentee'
        mentees = CustomUser.objects.filter(role='mentee').values('id', 'username', 'email')
        logger.info(f"Available mentees: {list(mentees)}")
        logger.info(f"Looking for mentee with ID: {mentee_id}")
            
        try:
            mentee = CustomUser.objects.get(id=mentee_id)
            logger.info(f"Found user: {mentee.id} - {mentee.username} (role: {mentee.role})")
            if mentee.role != 'mentee':
                logger.warning(f"User {mentee.id} has role '{mentee.role}', expected 'mentee'")
                raise CustomUser.DoesNotExist
            data['mentee_id'] = mentee.id
            return data
        except CustomUser.DoesNotExist:
            logger.error(f"Mentee with ID {mentee_id} not found or not a mentee")
            raise serializers.ValidationError({
                "mentee_id": f"Mentee with ID {mentee_id} not found or not a mentee. Available mentee IDs: {[m['id'] for m in mentees]}"
            })

    def create(self, validated_data):
        from users.models import CustomUser
        from django.core.exceptions import ValidationError
        
        # Remove both possible field names to avoid conflicts
        mentee_id = validated_data.pop('mentee_id', None) or validated_data.pop('mentee', None)
        
        try:
            mentee = CustomUser.objects.get(id=mentee_id, role='mentee')
        except CustomUser.DoesNotExist:
            raise ValidationError({"mentee_id": "Mentee not found"})
            
        # Add the mentor (current user) to the sprint
        validated_data['mentor'] = self.context['request'].user
        validated_data['mentee'] = mentee
        
        return super().create(validated_data)

        validated_data['mentee'] = mentee
        validated_data['mentor'] = self.context['request'].user
        return Sprint.objects.create(**validated_data)


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['sprint', 'title', 'description', 'due_date']


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['status', 'description']
        read_only_fields = ['sprint', 'title', 'due_date']