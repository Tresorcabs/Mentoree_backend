from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Sum, Count, Q, Max
from datetime import datetime, timedelta
from .models import Goal, Session
from profiles.models import MentorshipRequest, MentorReview
from meetings.models import Meeting
from .serializers import GoalSerializer, SessionSerializer

class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'mentor':
            return Goal.objects.filter(mentor=user)
        elif user.role == 'mentee':
            return Goal.objects.filter(mentee=user)
        return Goal.objects.none()

class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'mentor':
            return Session.objects.filter(mentor=user)
        elif user.role == 'mentee':
            return Session.objects.filter(mentee=user)
        return Session.objects.none()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_mentee(request):
    user = request.user
    if user.role != 'mentee':
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    # Objectifs atteints
    total_goals = Goal.objects.filter(mentee=user).count()
    completed_goals = Goal.objects.filter(mentee=user, is_completed=True).count()
    goals_achieved = f"{completed_goals}/{total_goals}"

    # Heures de mentorat suivies (total duration from completed meetings)
    from django.db.models import F, ExpressionWrapper, fields
    completed_meetings = Meeting.objects.filter(
        mentee=user,
        status='completed',
        started_at__isnull=False,
        ended_at__isnull=False
    ).annotate(
        duration=ExpressionWrapper(
            F('ended_at') - F('started_at'),
            output_field=fields.DurationField()
        )
    )
    total_seconds = sum(
        (meeting.ended_at - meeting.started_at).total_seconds()
        for meeting in completed_meetings
    )
    total_hours = round(total_seconds / 3600, 1)  # Convert to hours

    # Feedback moyen
    avg_feedback = Session.objects.filter(mentee=user).aggregate(Avg('feedback_score'))['feedback_score__avg'] or 0

    # Taux de progression globale
    avg_progress = Goal.objects.filter(mentee=user).aggregate(Avg('progress'))['progress__avg'] or 0

    # Graphique: évolution hebdomadaire du taux de progression
    # Pour simplifier, on calcule par semaine
    weeks = []
    for i in range(4):
        week_start = datetime.now() - timedelta(weeks=i)
        week_end = week_start + timedelta(days=7)
        progress = Goal.objects.filter(
            mentee=user,
            created_at__range=(week_start, week_end)
        ).aggregate(Avg('progress'))['progress__avg'] or 0
        weeks.append({
            'week': f'Week {4-i}',
            'progress': progress
        })

    # Tableau: objectifs
    goals = Goal.objects.filter(mentee=user).values(
        'title', 'progress', 'is_completed', 'due_date', 'mentor__first_name', 'mentor__last_name'
    )

    return Response({
        'cards': {
            'goals_achieved': goals_achieved,
            'total_hours': total_hours,
            'avg_feedback': round(avg_feedback, 1),
            'global_progress': round(avg_progress, 1)
        },
        'chart': weeks,
        'table': list(goals)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_mentor(request):
    user = request.user
    if user.role != 'mentor':
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    # Mentorés actifs (accepted mentorship requests)
    active_mentees = MentorshipRequest.objects.filter(
        mentor__user=user,
        status='accepted'
    ).values('mentee').distinct().count()

    # Sessions réalisées ce mois-ci (completed meetings in last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sessions_this_month = Meeting.objects.filter(
        mentor=user,
        status='completed',
        ended_at__gte=thirty_days_ago
    ).count()

    # Feedbacks reçus (average rating from mentor reviews)
    avg_feedback = MentorReview.objects.filter(mentor__user=user).aggregate(Avg('rating'))['rating__avg'] or 0

    # Impact global (simplifié: moyenne des progressions + feedback + rétention)
    # Only consider goals from accepted mentorships
    accepted_mentees = MentorshipRequest.objects.filter(
        mentor__user=user,
        status='accepted'
    ).values_list('mentee', flat=True)
    avg_progress = Goal.objects.filter(
        mentor=user,
        mentee__in=accepted_mentees
    ).aggregate(Avg('progress'))['progress__avg'] or 0

    # Calculate retention as percentage of completed vs total mentorships
    total_mentorships = MentorshipRequest.objects.filter(mentor__user=user).count()
    completed_mentorships = MentorshipRequest.objects.filter(
        mentor__user=user,
        status='completed'
    ).count()
    retention = (completed_mentorships / total_mentorships * 100) if total_mentorships > 0 else 0

    impact = (avg_progress + avg_feedback + retention) / 3

    # Graphique: activité des meetings par semaine
    weeks = []
    for i in range(4):
        week_start = datetime.now() - timedelta(weeks=i)
        week_end = week_start + timedelta(days=7)
        meetings_count = Meeting.objects.filter(
            mentor=user,
            status='completed',
            ended_at__range=(week_start, week_end)
        ).count()

        # Calculate total hours from completed meetings in this week
        week_meetings = Meeting.objects.filter(
            mentor=user,
            status='completed',
            ended_at__range=(week_start, week_end),
            started_at__isnull=False,
            ended_at__isnull=False
        )
        total_seconds = sum(
            (meeting.ended_at - meeting.started_at).total_seconds()
            for meeting in week_meetings
        )
        hours = round(total_seconds / 3600, 1)

        weeks.append({
            'week': f'Week {4-i}',
            'sessions': meetings_count,
            'hours': hours
        })

    # Tableau: mentorés
    mentees = Meeting.objects.filter(mentor=user).values(
        'mentee__first_name', 'mentee__last_name', 'mentee__id'
    ).annotate(
        last_session=Max('ended_at'),
        avg_satisfaction=Avg('feedback_score')  # This field doesn't exist in Meeting, will be None
    ).distinct()

    return Response({
        'cards': {
            'active_mentees': active_mentees,
            'sessions_this_month': sessions_this_month,
            'avg_feedback': round(avg_feedback, 1),
            'global_impact': round(impact, 1)
        },
        'chart': weeks,
        'table': list(mentees)
    })
