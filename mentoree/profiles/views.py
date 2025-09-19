#from Mentoree_backend.mentoree.utils.email_utils import send_mentorship_request_email
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models
from .models import MentorProfile, MenteeProfile, MentorshipRequest, MentorReview
from .serializers import (
    MentorProfileListSerializer,
    MentorProfileDetailSerializer,
    MenteeProfileSerializer,
    MentorshipRequestSerializer,
    MentorReviewSerializer,
    MentorProfileUpdateSerializer
)
from .filters import MentorProfileFilter
#from mentoree.utils.email_utils import send_mentorship_request_email




class MentorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving mentors.
    Supports filtering, searching and ordering.
    """
    queryset = MentorProfile.objects.filter(is_active=True, user__is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_class = MentorProfileFilter
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'expertise']
    ordering_fields = ['average_rating', 'total_reviews', 'years_of_experience', 'hourly_rate']
    ordering = ['-is_featured', '-average_rating']  # Default ordering
    pagination_class = None  # Disable pagination for now to debug the issue

    def get_queryset(self):
        queryset = super().get_queryset()

        # Handle custom ordering from frontend
        ordering_param = self.request.query_params.get('ordering')
        if ordering_param:
            if ordering_param == 'price-asc':
                queryset = queryset.order_by('hourly_rate')
            elif ordering_param == 'price-desc':
                queryset = queryset.order_by('-hourly_rate')
            elif ordering_param == 'rating':
                queryset = queryset.order_by('-average_rating')
            elif ordering_param == 'experience':
                queryset = queryset.order_by('-years_of_experience')
            elif ordering_param == 'relevance':
                # Default relevance ordering
                queryset = queryset.order_by('-is_featured', '-average_rating', '-total_reviews')

        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MentorProfileDetailSerializer
        return MentorProfileListSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """
        Toggle favorite status of a mentor for the current mentee
        """
        mentor = self.get_object()
        mentee = request.user.mentee_profile
        
        if mentor in mentee.favorite_mentors.all():
            mentee.favorite_mentors.remove(mentor)
            return Response({'status': 'removed from favorites'})
        else:
            mentee.favorite_mentors.add(mentor)
            return Response({'status': 'added to favorites'})
    

class MentorshipRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing mentorship requests.
    """
    serializer_class = MentorshipRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination to return plain arrays
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'mentor':
            return MentorshipRequest.objects.filter(mentor__user=user)
        else:
            return MentorshipRequest.objects.filter(mentee__user=user)
    
    @action(detail=False, methods=['get'])
    def mentor_requests(self, request):
        """
        Get all mentorship requests for the current mentor with detailed information
        """
        if request.user.role != 'mentor':
            return Response(
                {'error': 'Only mentors can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = MentorshipRequest.objects.filter(mentor__user=request.user)
        
        # Apply filters if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Apply search if provided
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(mentee__user__first_name__icontains=search) |
                models.Q(mentee__user__last_name__icontains=search) |
                models.Q(message__icontains=search) |
                models.Q(objectives__icontains=search)
            )
        
        # Apply ordering if provided
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a message to the mentee
        """
        mentorship_request = self.get_object()
        message = request.data.get('message')
        
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In a real implementation, this would send a message to the mentee
        # For now, we'll just return a success response
        
        return Response({'status': 'message sent'})
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update the status of a mentorship request
        """
        request_obj = self.get_object()
        new_status = request.data.get('status')

        if new_status not in ['accepted', 'rejected', 'completed', 'cancelled']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only mentor can accept/reject
        if new_status in ['accepted', 'rejected'] and request.user != request_obj.mentor.user:
            return Response(
                {'error': 'Only the mentor can accept or reject requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only mentee can cancel
        if new_status == 'cancelled' and request.user != request_obj.mentee.user:
            return Response(
                {'error': 'Only the mentee can cancel requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update the request
        old_status = request_obj.status
        request_obj.status = new_status
        request_obj.updated_at = timezone.now()
        request_obj.save()

        # Send email notification based on status change
        # if new_status == 'accepted' and old_status != 'accepted':
        #     send_mentorship_request_email(request_obj.id, 'accepted')
        # elif new_status == 'rejected' and old_status != 'rejected':
        #     send_mentorship_request_email(request_obj.id, 'rejected')

        return Response({'status': 'updated'})

class MentorReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing mentor reviews.
    """
    serializer_class = MentorReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MentorReview.objects.filter(
            mentorship_request__status='completed',
            mentorship_request__mentee__user=self.request.user
        )
    
    def perform_create(self, serializer):
        request_id = self.request.data.get('mentorship_request')
        try:
            mentorship_request = MentorshipRequest.objects.get(
                id=request_id,
                status='completed',
                mentee__user=self.request.user
            )
            serializer.save(
                mentorship_request=mentorship_request,
                mentor=mentorship_request.mentor,
                mentee=mentorship_request.mentee
            )
        except MentorshipRequest.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or incomplete mentorship request"
            )

class MenteeProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing mentee profiles.
    """
    serializer_class = MenteeProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'mentor':
            # Mentors can only see mentees they are mentoring
            return MenteeProfile.objects.filter(
                sent_requests__mentor__user=user,
                sent_requests__status='accepted'
            ).distinct()
        else:
            # Mentees can only see their own profile
            return MenteeProfile.objects.filter(user=user)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_mentor_profile(request):
    """
    Update mentor profile fields for the authenticated user
    """
    if request.user.role != 'mentor':
        return Response({"error": "Only mentors can update mentor profiles"}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        mentor_profile = MentorProfile.objects.get(user=request.user)
    except MentorProfile.DoesNotExist:
        # Create a new mentor profile if it doesn't exist
        mentor_profile = MentorProfile.objects.create(user=request.user)
    
    serializer = MentorProfileUpdateSerializer(mentor_profile, data=request.data, partial=True)
    
    if serializer.is_valid():
        # Make sure expertise is saved as a list
        if 'expertise' in request.data:
            if isinstance(request.data['expertise'], list):
                serializer.validated_data['expertise'] = request.data['expertise']
            else:
                serializer.validated_data['expertise'] = [request.data['expertise']]
            
        # Make sure languages is saved as a list
        if 'languages' in request.data:
            if isinstance(request.data['languages'], list):
                serializer.validated_data['languages'] = request.data['languages']
            else:
                serializer.validated_data['languages'] = [request.data['languages']]
            
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
