from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser

class MentorProfile(models.Model):
    """
    Model to store additional information about mentors.
    This includes expertise, availability, ratings, and other mentor-specific data.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='mentor_profile')
    expertise = models.JSONField(blank=True, null=True)  # Store as array of expertise areas
    years_of_experience = models.PositiveIntegerField(default=0)
    linked_in_profile = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)  # Could be a JSON field
    availability = models.JSONField(blank=True, null=True)  # Store availability schedule
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)  # For "Top Mentor" badge
    is_new = models.BooleanField(default=True)  # For "New Mentor" badge
    location = models.CharField(max_length=255, blank=True, null=True)
    languages = models.JSONField(blank=True, null=True)  # Store spoken languages

    def __str__(self):
        return f'Mentor Profile of {self.user.username}'

    class Meta:
        indexes = [
            models.Index(fields=['average_rating']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_new']),
        ]

class MenteeProfile(models.Model):
    """
    Model to store additional information about mentees.
    This includes goals, interests, and other mentee-specific data.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='mentee_profile')
    study_field = models.CharField(max_length=255, blank=True, null=True)
    current_level = models.CharField(max_length=50, blank=True, null=True)
    goals = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    interests = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    favorite_mentors = models.ManyToManyField(MentorProfile, related_name='favorited_by', blank=True)

    def __str__(self):
        return f'Mentee Profile of {self.user.username}'

class MentorshipRequest(models.Model):
    """
    Model to handle mentorship requests between mentees and mentors.
    Tracks the status and details of mentorship arrangements.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='mentorship_requests')
    mentee = models.ForeignKey(MenteeProfile, on_delete=models.CASCADE, related_name='sent_requests')
    message = models.TextField()  # Motivation letter
    objectives = models.TextField(blank=True, null=True)  # Mentorship objectives
    duration = models.CharField(max_length=100, blank=True, null=True)  # Desired mentorship duration
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_generated = models.BooleanField(default=False)  # Track if message was AI-generated

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Request from {self.mentee.user.username} to {self.mentor.user.username}'

class MentorReview(models.Model):
    """
    Model to store reviews and ratings for mentors.
    Allows mentees to provide feedback after mentorship.
    """
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='reviews')
    mentee = models.ForeignKey(MenteeProfile, on_delete=models.CASCADE, related_name='given_reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    mentorship_request = models.OneToOneField(
        MentorshipRequest, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='review'
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ['mentee', 'mentorship_request']  # One review per mentorship
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        # Update mentor's average rating on save
        super().save(*args, **kwargs)
        mentor = self.mentor
        reviews = mentor.reviews.all()
        mentor.average_rating = sum(r.rating for r in reviews) / len(reviews)
        mentor.total_reviews = len(reviews)
        mentor.save()

    def __str__(self):
        return f'Review by {self.mentee.user.username} for {self.mentor.user.username}'


class Goal(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mentor_goals')
    mentee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mentee_goals')
    progress = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Goal: {self.title} ({self.mentee.username})'


class Session(models.Model):
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions_led')
    mentee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions_attended')
    duration = models.FloatField(help_text="Durée en heures")
    date = models.DateTimeField()
    feedback_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'Session: {self.mentor.username} -> {self.mentee.username} ({self.date})'