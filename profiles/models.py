from django.db import models
from users.models import CustomUser

# Create your models here.
class MentorProfile(models.Model):
    """
    Model to store additional information about mentors.
    This can include fields like expertise, availability, etc.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='mentor_profile')
    expertise = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    linked_in_profile = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)  # Could be a JSON field
    availability = models.TextField(blank=True, null=True)  # Could be a JSON field in the future
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Mentor Profile of {self.user.username}'

class MenteeProfile(models.Model):
    """
    Model to store additional information about mentees.
    This can include fields like goals, interests, etc.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='mentee_profile')
    study_field = models.CharField(max_length=255, blank=True, null=True)  # ex: 'Informatique', 'Marketing'
    current_level = models.CharField(max_length=50, blank=True, null=True)  # ex: 'Licence', 'Master'
    goals = models.TextField(blank=True, null=True)  # les objectifs du mentoré ex: [ 'Apprendre Python', 'Développer un projet' ]
    skills = models.TextField(blank=True, null=True)  # les compétences du mentoré
    interests = models.TextField(blank=True, null=True) # les intérêts du mentoré ex: [ 'Développement Web', 'Data Science' ]
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Mentee Profile of {self.user.username}'