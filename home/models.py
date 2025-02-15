from django.contrib.auth.models import User
from django.db import models
import uuid
import datetime
from googleapiclient.discovery import build




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
    pod = models.ForeignKey(Pod, related_name="pod_bookings_v1", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_bookings_v1", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    hours = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_type = models.CharField(max_length=100, choices=(
        ('Pre Paid', 'Pre Paid'),
        ('Post Paid', 'Post Paid')
    ))
    status = models.CharField(max_length=20, choices=(
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ), default='active')
    calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    check_in_time = models.CharField(max_length=5, default='14:00')
    
    def __str__(self) -> str:
        return f'{self.pod.pod_name} - {self.user.username}'

    def get_hours(self):
        if hasattr(self, 'hours'):
            return self.hours
        return getattr(self, 'hours', 1)

    def create_calendar_event(self):
        """Tạo sự kiện trên Google Calendar"""
        if not self.calendar_event_id and self.status in ['completed', 'active']:
            try:
                service = get_calendar_service()
                event = {
                    'summary': f'Đặt phòng: {self.pod.pod_name}',
                    'location': 'Pod Hotel',
                    'description': f'Số giờ: {self.hours}\nTổng tiền: {self.total_amount} VNĐ',
                    'start': {
                        'dateTime': f'{self.start_date}T{self.check_in_time}:00',
                        'timeZone': 'Asia/Ho_Chi_Minh',
                    },
                    'end': {
                        'dateTime': (datetime.datetime.combine(self.start_date, 
                                   datetime.datetime.strptime(self.check_in_time, '%H:%M').time()) 
                                   + datetime.timedelta(hours=self.hours)).strftime('%Y-%m-%dT%H:%M:00'),
                        'timeZone': 'Asia/Ho_Chi_Minh',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 60},
                        ],
                    },
                }
                
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                self.calendar_event_id = created_event['id']
                self.save()
                return True
            except Exception as e:
                print(f"Lỗi khi tạo sự kiện calendar: {str(e)}")
                return False
        return False

    def update_calendar_event(self):
        """Cập nhật sự kiện trên Google Calendar"""
        if self.calendar_event_id:
            try:
                service = get_calendar_service()
                event = service.events().get(calendarId='primary', 
                                          eventId=self.calendar_event_id).execute()
                
                event['summary'] = f'Đặt phòng: {self.pod.pod_name}'
                event['description'] = f'Số giờ: {self.hours}\nTổng tiền: {self.total_amount} VNĐ'
                event['status'] = 'cancelled' if self.status == 'cancelled' else 'confirmed'
                
                updated_event = service.events().update(calendarId='primary',
                                                      eventId=self.calendar_event_id,
                                                      body=event).execute()
                return True
            except Exception as e:
                print(f"Lỗi khi cập nhật sự kiện calendar: {str(e)}")
                return False
        return False

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

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Đang chờ'),
        ('completed', 'Thành công'), 
        ('failed', 'Thất bại')
    )
    
    PAYMENT_METHODS = (
        ('vnpay', 'VNPay'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Người dùng')
    pod = models.ForeignKey('Pod', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name='Phòng')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Số tiền')
    description = models.TextField(verbose_name='Mô tả', blank=True)
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHODS, 
        default='vnpay',
        verbose_name='Phương thức thanh toán'
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Mã giao dịch')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending', verbose_name='Trạng thái')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')

    class Meta:
        verbose_name = 'Payments'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.get_status_display()}"

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    pod = models.ForeignKey(Pod, related_name="pod_bookings_v2", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_bookings_v2", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    hours = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_type = models.CharField(max_length=100, choices=(
        ('Pre Paid', 'Pre Paid'),
        ('Post Paid', 'Post Paid')
    ))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    def __str__(self) -> str:
        return f'{self.pod.pod_name} - {self.user.username}'

    def get_hours(self):
        if hasattr(self, 'hours'):
            return self.hours
        return getattr(self, 'hours', 1)