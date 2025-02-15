# Pod Booking System

Hệ thống đặt phòng Pod tích hợp thanh toán VNPay và Google Calendar.

## Yêu cầu hệ thống

- Docker và Docker Compose
- Python 3.9+
- PostgreSQL
- VNPay Sandbox account
- Google Calendar API credentials

## Cài đặt và Chạy

### 1. Clone repository
bash
git clone <repository-url>
### 2. Tạo và kích hoạt môi trường ảo
- Tạo môi trường ảo
python -m venv venv
- Kích hoạt môi trường ảo
venv\Scripts\activate
- Kiểm tra python version
python --version
### 3. Khởi động với Docker
- Build và chạy containers
docker-compose up --build
- Chạy migrations
docker-compose exec web python manage.py migrate
- Tạo superuser
docker-compose exec web python manage.py createsuperuser
### 4. Truy cập ứng dụng

- Website: http://localhost:8000
- Admin panel: http://localhost:8000/admin
## Tính năng chính

1. **Quản lý Pod**
   - Xem danh sách Pod
   - Đặt Pod theo giờ
   - Xem chi tiết và trạng thái Pod

2. **Đặt chỗ và Thanh toán**
   - Đặt Pod theo thời gian
   - Thanh toán qua VNPay
   - Xác nhận đặt chỗ

3. **Tích hợp Calendar**
   - Đồng bộ với Google Calendar
   - Nhận thông báo lịch hẹn

## Quản lý Docker
- Khởi động containers
docker-compose up
- Chạy ở chế độ nền
docker-compose up -d
- Dừng containers
docker-compose down
- Xem logs
docker-compose logs
- Xem logs của service cụ thể
docker-compose logs web
- Rebuild sau khi thay đổi
docker-compose up --build
