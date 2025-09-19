from rest_framework import serializers
from .models import MentorProfile, MenteeProfile, MentorshipRequest, MentorReview
from users.serializers import CustomUserSerializer

class MentorReviewSerializer(serializers.ModelSerializer):
    mentee_name = serializers.CharField(source='mentee.user.username', read_only=True)
    mentee_picture = serializers.URLField(source='mentee.user.profile_picture', read_only=True)
    
    class Meta:
        model = MentorReview
        fields = [
            'id',
            'rating',
            'comment',
            'created_at',
            'mentee_name',
            'mentee_picture'
        ]

class MentorProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing mentors with essential information
    """
    user = CustomUserSerializer(read_only=True)
    total_mentees = serializers.SerializerMethodField()
    
    class Meta:
        model = MentorProfile
        fields = [
            'id',
            'user',
            'expertise',
            'years_of_experience',
            'availability',
            'average_rating',
            'total_reviews',
            'is_featured',
            'is_new',
            'location',
            'languages',
            'hourly_rate',
            'total_mentees'
        ]
    
    def get_total_mentees(self, obj):
        return obj.mentorship_requests.filter(status='accepted').count()

class MentorProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed mentor profile view
    """
    user = CustomUserSerializer(read_only=True)
    reviews = MentorReviewSerializer(many=True, read_only=True)
    total_mentees = serializers.SerializerMethodField()
    
    class Meta:
        model = MentorProfile
        fields = [
            'id',
            'user',
            'expertise',
            'years_of_experience',
            'linked_in_profile',
            'website',
            'certifications',
            'availability',
            'average_rating',
            'total_reviews',
            'reviews',
            'is_featured',
            'is_new',
            'location',
            'languages',
            'hourly_rate',
            'total_mentees'
        ]
    
    def get_total_mentees(self, obj):
        return obj.mentorship_requests.filter(status='accepted').count()

class MenteeProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    favorite_mentors = MentorProfileListSerializer(many=True, read_only=True)
    
    class Meta:
        model = MenteeProfile
        fields = [
            'id',
            'user',
            'study_field',
            'current_level',
            'goals',
            'skills',
            'interests',
            'favorite_mentors'
        ]

class MentorshipRequestSerializer(serializers.ModelSerializer):
    mentor = MentorProfileListSerializer(read_only=True)
    mentor_id = serializers.IntegerField(write_only=True)
    mentee = MenteeProfileSerializer(read_only=True)
    
    class Meta:
        model = MentorshipRequest
        fields = [
            'id',
            'mentor',
            'mentor_id',
            'mentee',
            'message',
            'objectives',
            'duration',
            'status',
            'created_at',
            'updated_at',
            'ai_generated'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        mentor_id = validated_data.pop('mentor_id')
        mentor = MentorProfile.objects.get(id=mentor_id)
        user = self.context['request'].user

        # Get or create mentee profile
        try:
            mentee = user.mentee_profile
        except MenteeProfile.DoesNotExist:
            # Create mentee profile if it doesn't exist
            mentee = MenteeProfile.objects.create(user=user)

        # Check if request already exists
        if MentorshipRequest.objects.filter(mentor=mentor, mentee=mentee, status__in=['pending', 'accepted']).exists():
            raise serializers.ValidationError("You already have a pending or accepted request with this mentor")

        return MentorshipRequest.objects.create(
            mentor=mentor,
            mentee=mentee,
            **validated_data
        )

class MentorProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating mentor profile fields
    """
    class Meta:
        model = MentorProfile
        fields = [
            'expertise',
            'years_of_experience',
            'linked_in_profile',
            'website',
            'certifications',
            'availability',
            'hourly_rate',
            'location',
            'languages'
        ]
        read_only_fields = ['is_featured', 'is_new', 'average_rating', 'total_reviews']