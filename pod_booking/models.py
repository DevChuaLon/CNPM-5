from django.db import models

class Pod(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
