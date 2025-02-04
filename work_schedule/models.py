from django.db import models

class WorkSchedule(models.Model):
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    start_time = models.DateTimeField(verbose_name="Thời gian bắt đầu")
    end_time = models.DateTimeField(verbose_name="Thời gian kết thúc")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    def __str__(self):
        return self.title
