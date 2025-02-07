from django.contrib.auth.models import User
from django.db import models
import uuid




class BaseModel(models.Model):
    uid = models.UUIDField(default=uuid.uuid4   , editable=False , primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering=['uid']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.user.username
    
class Amenities(BaseModel):
    amenity_name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.amenity_name

class Pod(BaseModel):
    pod_name = models.CharField(max_length=100)
    pod_price = models.IntegerField()
    description = models.TextField()
    amenities = models.ManyToManyField(Amenities)
    room_count = models.IntegerField(default=10)
    
    def __str__(self) -> str:
        return self.pod_name

class PodImages(BaseModel):
    pod = models.ForeignKey(Pod, related_name='pod_images', on_delete=models.CASCADE)
    images = models.ImageField(upload_to='pods')

class PodBooking(BaseModel):
    pod = models.ForeignKey(Pod, related_name="pod_bookings", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_bookings", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    booking_type = models.CharField(max_length=100, choices=(
        ('Pre Paid', 'Pre Paid'),
        ('Post Paid', 'Post Paid')
    ))
    status = models.CharField(max_length=20, choices=(
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ), default='active')
    
    def __str__(self) -> str:
        return f'{self.pod.pod_name} - {self.user.username}'