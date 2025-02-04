from django.db import models
from accounts.models import CustomUser

class Feedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    rating = models.PositiveIntegerField()  # Rating từ 1-5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.username} - Rating: {self.rating}"
