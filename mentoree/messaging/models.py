from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from users.models import CustomUser
from profiles.models import MentorProfile, MenteeProfile


class Conversation(models.Model):
    """
    Model to represent a conversation between two users (mentor and mentee).
    """
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='conversations')
    mentee = models.ForeignKey(MenteeProfile, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['mentor', 'mentee']
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation: {self.mentor.user.username} ↔ {self.mentee.user.username}"

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """
    Model to represent individual messages in a conversation.
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('task', 'Task Update'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True, null=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # For file messages
    file = models.FileField(
        upload_to='message_files/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'])]
    )
    file_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"

    def mark_as_read(self):
        """Mark message as read and set read timestamp"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class Task(models.Model):
    """
    Model to represent mentorship tasks assigned by mentor to mentee.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Proof of completion
    proof_file = models.FileField(
        upload_to='task_proofs/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip'])]
    )
    proof_description = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Task: {self.title} ({self.status})"

    def mark_completed(self, proof_file=None, proof_description=None):
        """Mark task as completed with proof"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        if proof_file:
            self.proof_file = proof_file
        if proof_description:
            self.proof_description = proof_description
        self.save()


class UserStatus(models.Model):
    """
    Model to track user online/offline status and last activity.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    current_room = models.CharField(max_length=100, blank=True, null=True)  # For tracking active conversation

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.user.username}: {status}"

    def set_online(self, room=None):
        """Set user as online"""
        self.is_online = True
        if room:
            self.current_room = room
        self.save(update_fields=['is_online', 'last_seen', 'current_room'])

    def set_offline(self):
        """Set user as offline"""
        self.is_online = False
        self.current_room = None
        self.save(update_fields=['is_online', 'last_seen', 'current_room'])
