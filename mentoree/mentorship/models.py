from django.db import models
from users.models import CustomUser as User

class Goal(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_goals')
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentee_goals')
    progress = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.mentee.username}"

class Session(models.Model):
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions_led')
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions_attended')
    duration = models.FloatField(help_text="Durée en heures")
    date = models.DateTimeField()
    feedback_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.mentor.username} -> {self.mentee.username} on {self.date}"
