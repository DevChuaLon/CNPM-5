from django.db import models
from accounts.models import CustomUser

class Priority(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=20, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.priority_level}"
