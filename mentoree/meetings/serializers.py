from rest_framework import serializers
from .models import Meeting

class MeetingSerializer(serializers.ModelSerializer):
    mentor_name = serializers.CharField(source='mentor.username', read_only=True)
    mentee_name = serializers.CharField(source='mentee.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Meeting
        fields = [
            'id', 'mentor', 'mentee', 'mentor_name', 'mentee_name',
            'scheduled_at', 'room_url', 'recording_url', 'status', 'status_display',
            'started_at', 'ended_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'room_url', 'recording_url', 'started_at', 'ended_at']