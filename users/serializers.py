from rest_framework import serializers
from .models import CustomUser
from profiles.models import MentorProfile, MenteeProfile
from dj_rest_auth.registration.serializers import RegisterSerializer 

# serializer for MentorProfile
class MentorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        fields = [
                'expertise',
                'years_of_experience',
                'linked_in_profile',
                'website',
                'certifications',
                'availability',
                ]

# serializer for MenteeProfile
class MenteeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenteeProfile
        fields = [
                'study_field',
                'current_level',
                'goals',
                'skills',
                'interests',
                ]

# serializer for CustomUser
class CustomUserSerializer(serializers.ModelSerializer):
    # Intégration des profils de mentor et mentoré 
    mentor_profile = MentorProfileSerializer(read_only=True)
    mentee_profile = MenteeProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        # Champs à exposer dans la réponse
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'date_of_birth',
            'bio',
            'city',
            'profile_picture',
            'phone',
            'is_verified',
            'is_online',
            'is_active',
            'date_joined',
            'is_profile_complete',
            'mentor_profile',
            'mentee_profile'
        ]
        read_only_fields = ['id', 'is_active', 'date_joined', 'is_profile_complete', 'is_verified', 'is_online']
        
    # Validation personnalisée d'email et username
    def validate_email(self, value):
        """
        Vérifie que l'email est unique.
        """
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate_username(self, value):
        """
        Vérifie que le nom d'utilisateur est unique.
        """
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

# Custom Register Serializer to include phone field
class CustomRegisterSerializer(RegisterSerializer):
    phone = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[('mentor', 'Mentor'), ('mentee', 'Mentoré')], required=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['phone'] = self.validated_data.get('phone', '')
        data['role'] = self.validated_data.get('role', '')
        return data
