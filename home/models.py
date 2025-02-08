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

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('booking', 'Đặt phòng'),
        ('system', 'Hệ thống'),
        ('update', 'Cập nhật'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @classmethod
    def create_notification(cls, user, type, title, message):
        return cls.objects.create(
            user=user,
            type=type,
            title=title,
            message=message
        )

class AdminNotification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)

    def send_to_all_users(self):
        users = User.objects.all()
        for user in users:
            Notification.objects.create(
                user=user,
                type='admin',
                title=self.title,
                message=self.message
            )
        self.is_sent = True
        self.save()

    def __str__(self):
        return f"Admin Notification: {self.title}"

class Review(BaseModel):
    pod = models.ForeignKey(Pod, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 sao
    comment = models.TextField()
    
    def __str__(self):
        return f"{self.user.username}'s review for {self.pod.pod_name}"

    class Meta:
        ordering = ['-created_at']

class Feedback(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Người dùng')
    pod = models.ForeignKey('Pod', on_delete=models.CASCADE, verbose_name='Phòng')
    rating = models.IntegerField(choices=[(i, f'{i} sao') for i in range(1, 6)], verbose_name='Đánh giá')
    comment = models.TextField(verbose_name='Nhận xét')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian tạo')

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
        ordering = ['-created_at']

    def __str__(self):
        return f'Feedback của {self.user.username} về {self.pod.pod_name}'