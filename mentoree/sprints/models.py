from django.db import models
from users.models import CustomUser


class Sprint(models.Model):
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_sprints')
    mentee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='assigned_sprints')
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    objectives = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sprint: {self.title} ({self.mentor.username} -> {self.mentee.username})"


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Task: {self.title} ({self.status})"
