from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models
from .models import Meeting
from .serializers import MeetingSerializer
from .utils.daily import create_daily_room, get_room_recordings

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_meeting(request):
    """
    Create a new meeting with Daily.co room.
    Only mentors can create meetings.
    Expected data: mentor_id, mentee_id, scheduled_at
    """
    # Check if user is a mentor
    if request.user.role != 'mentor':
        return Response(
            {'error': 'Only mentors can create meetings'},
            status=status.HTTP_403_FORBIDDEN
        )

    data = request.data
    mentor_id = data.get('mentor_id')
    mentee_id = data.get('mentee_id')
    scheduled_at = data.get('scheduled_at')

    if not all([mentor_id, mentee_id, scheduled_at]):
        return Response(
            {'error': 'mentor_id, mentee_id, and scheduled_at are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Ensure the mentor_id matches the current user
    if int(mentor_id) != request.user.id:
        return Response(
            {'error': 'You can only create meetings where you are the mentor'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        # Create the meeting instance
        meeting = Meeting.objects.create(
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            scheduled_at=scheduled_at
        )

        # Create Daily room
        room_url = create_daily_room()
        meeting.room_url = room_url
        meeting.save()

        serializer = MeetingSerializer(meeting)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting(request, meeting_id):
    """
    Get meeting details by ID.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)
    serializer = MeetingSerializer(meeting)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_meetings(request):
    """
    Get all meetings for the current user (as mentor or mentee).
    """
    user = request.user
    meetings = Meeting.objects.filter(
        models.Q(mentor=user) | models.Q(mentee=user)
    ).order_by('-scheduled_at')

    serializer = MeetingSerializer(meetings, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_meeting(request, meeting_id):
    """
    Mark a meeting as started.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)

    # Check if user has access to this meeting
    if request.user != meeting.mentor and request.user != meeting.mentee:
        return Response(
            {'error': 'Access denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    if meeting.status != 'scheduled':
        return Response(
            {'error': 'Meeting cannot be started'},
            status=status.HTTP_400_BAD_REQUEST
        )

    meeting.status = 'in_progress'
    meeting.started_at = models.timezone.now()
    meeting.save()

    serializer = MeetingSerializer(meeting)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_meeting(request, meeting_id):
    """
    Mark a meeting as completed and fetch recordings.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)

    # Check if user has access to this meeting
    if request.user != meeting.mentor and request.user != meeting.mentee:
        return Response(
            {'error': 'Access denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    if meeting.status != 'in_progress':
        return Response(
            {'error': 'Meeting is not in progress'},
            status=status.HTTP_400_BAD_REQUEST
        )

    meeting.status = 'completed'
    meeting.ended_at = models.timezone.now()
    meeting.save()

    # Try to get recordings
    if meeting.room_url:
        recordings = get_room_recordings(meeting.room_url)
        if recordings:
            # For simplicity, take the first recording URL
            # In a real app, you might want to store multiple recordings
            meeting.recording_url = recordings[0].get('download_url') if recordings[0] else None
            meeting.save()

    serializer = MeetingSerializer(meeting)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_recordings(request, meeting_id):
    """
    Get recordings for a specific meeting.
    """
    meeting = get_object_or_404(Meeting, id=meeting_id)

    # Check if user has access to this meeting
    if request.user != meeting.mentor and request.user != meeting.mentee:
        return Response(
            {'error': 'Access denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    recordings = get_room_recordings(meeting.room_url)
    return Response({'recordings': recordings})
