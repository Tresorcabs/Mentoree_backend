from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    """
    Custom user model that extends the default Django user model.
    This can be used to add additional fields or methods specific to the application.
    """
    ROLES_CHOICES = [
        ('mentor', 'Mentor'),
        ('mentee', 'Mentoré'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLES_CHOICES)
    email = models.EmailField(unique=True)  # Ensure email is unique
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=False)  # To manage user activation status
    is_verified = models.BooleanField(default=False)  # To manage email verification status
    is_online = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)  # Automatically set the date when the user is created

    is_profile_complete = models.BooleanField(default=False)  # To check if the user has completed their profile
    
    username = models.CharField(max_length=150, unique=True)  # Ensure username is unique
    
    USERNAME_FIELD = 'email'  # Use email as the unique identifier for authentication
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']  # Fields required for creating a user
    
    def __str__(self):
        return f'{self.username} ({self.role})'