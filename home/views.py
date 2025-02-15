from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout, login
from django.contrib import messages
from django.contrib.auth.models import User
from . models import *
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import datetime
import hashlib
import hmac
import urllib.parse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import uuid
from .utils import generate_vnpay_payment_url, get_calendar_service, SCOPES
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from django.urls import reverse
import os
import pickle
import json
import random
import pytz

# Thêm dòng này ở đầu file, sau các import
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Cho phép HTTP trong môi trường development

def check_booking(uid, room_count, start_date, end_date):
    try:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        qs = PodBooking.objects.filter(
            pod__uid=uid,
            status='active'
        ).filter(
            Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
        )
        
        return len(qs) < room_count
    except (ValueError, TypeError):
        return False

def signin(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Đăng nhập thành công')
            return redirect('index')
        
        messages.error(request, 'Tài khoản hoặc mật khẩu không đúng')
    
    return render(request, 'home/signin.html')

def signup(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Kiểm tra xác nhận mật khẩu
        if password != confirm_password:
            messages.error(request, 'Mật khẩu xác nhận không khớp!')
            return render(request, 'home/signup.html')
            
        # Kiểm tra username đã tồn tại
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại!')
            return render(request, 'home/signup.html')
            
        # Kiểm tra email đã tồn tại
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email đã được sử dụng!')
            return render(request, 'home/signup.html')
            
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
            return redirect('signin')
            
        except Exception as e:
            messages.error(request, 'Đã xảy ra lỗi khi tạo tài khoản!')
            return render(request, 'home/signup.html')
            
    return render(request, 'home/signup.html')

def signout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Đăng xuất thành công')
    return redirect('index')

def index(request):
    try:
        # Lấy tất cả khách sạn và sắp xếp theo giá
        pods = Pod.objects.all().order_by('pod_price')
        amenities = Amenities.objects.all()
        
        # Xử lý tìm kiếm và lọc
        selected_amenities = request.GET.getlist('selectAmenity')
        sort_by = request.GET.get('sortSelect')
        search = request.GET.get('searchInput')
        
        # Sửa lại phần này - Chỉ lọc nếu không phải "Tất cả loại phòng" và có chọn amenity
        if selected_amenities and selected_amenities[0] != "Tất cả loại phòng":
            pods = pods.filter(amenities__amenity_name__in=selected_amenities).distinct()
        
        if search:
            pods = pods.filter(
                Q(pod_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if sort_by == 'low_to_high':
            pods = pods.order_by('pod_price')
        elif sort_by == 'high_to_low':
            pods = pods.order_by('-pod_price')
            
        # Thêm phân trang
        paginator = Paginator(pods, 6)  # 6 phòng mỗi trang
        page = request.GET.get('page', 1)
        pods = paginator.get_page(page)
        
        # Lấy tất cả booking của user hiện tại
        if request.user.is_authenticated:
            bookings = PodBooking.objects.filter(user=request.user)
            calendar_events = []
            
            for booking in bookings:
                event = {
                    'title': booking.pod.pod_name,  # Tên phòng
                    'start': booking.start_date.strftime('%Y-%m-%d'),  # Ngày đặt
                    'hours': booking.hours,  # Số giờ đặt
                    'backgroundColor': '#28a745',  # Màu nền cho event
                    'borderColor': '#28a745',  # Màu viền
                    'textColor': '#ffffff'  # Màu chữ
                }
                calendar_events.append(event)
        else:
            calendar_events = []
        
        context = {
            'pods': pods,
            'amenities': amenities,
            'selected_amenities': selected_amenities,
            'sort_by': sort_by,
            'search': search,
            'today': date.today().strftime('%Y-%m-%d'),
            'calendar_events': json.dumps(calendar_events)
        }
        
        return render(request, 'home/index.html', context)
        
    except Exception as e:
        messages.error(request, 'Đã xảy ra lỗi khi tải trang chủ')
        return render(request, 'home/index.html', {
            'today': date.today().strftime('%Y-%m-%d')
        })

@login_required
def user_profile(request):
    try:
        # Lấy hoặc tạo profile cho user
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Lấy thông tin đặt phòng
        bookings = PodBooking.objects.filter(user=request.user)
        total_bookings = bookings.count()
        active_bookings = bookings.filter(status='active').count()
        recent_bookings = bookings.order_by('-created_at')[:5]
        
        # Kiểm tra kết nối Google Calendar
        is_calendar_connected = os.path.exists(settings.GOOGLE_CALENDAR_TOKEN_PATH)
        
        context = {
            'user': request.user,
            'profile': profile,
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'recent_bookings': recent_bookings,
            'today': date.today(),
            'is_calendar_connected': is_calendar_connected
        }
        
        return render(request, 'home/profile.html', context)
        
    except Exception as e:
        messages.error(request, f'Đã xảy ra lỗi khi tải trang profile: {str(e)}')
        return redirect('index')

@login_required
def booking_history(request):
    try:
        # Lấy tất cả các đặt phòng của user hiện tại
        bookings = PodBooking.objects.filter(
            user=request.user
        ).select_related('pod').order_by('-created_at')
        
        # Lọc theo trạng thái nếu có
        status = request.GET.get('status')
        if status:
            bookings = bookings.filter(status=status)
        
        # Tính toán số giờ và tổng tiền cho mỗi booking
        for booking in bookings:
            if not hasattr(booking, 'hours'):
                booking.hours = booking.get_hours()
            
            if not hasattr(booking, 'total_amount'):
                booking.total_amount = booking.pod.pod_price * booking.hours

            # Đặt giờ mặc định nếu không có
            if not hasattr(booking, 'check_in_time'):
                booking.check_in_time = '14:00'
        
        context = {
            'bookings': bookings,
            'total_bookings': bookings.count(),
            'active_bookings': bookings.filter(status='active').count(),
            'cancelled_bookings': bookings.filter(status='cancelled').count(),
            'completed_bookings': bookings.filter(status='completed').count(),
            'today': date.today().strftime('%Y-%m-%d'),
            'current_status': status,
            'status_choices': PodBooking._meta.get_field('status').choices
        }
        
        return render(request, 'home/booking_history.html', context)
        
    except Exception as e:
        messages.error(request, f'Đã xảy ra lỗi khi tải lịch sử đặt phòng: {str(e)}')
        return redirect('index')

@login_required
def cancel_booking(request, booking_id):
    try:
        booking = get_object_or_404(PodBooking, uid=booking_id, user=request.user)
        if booking.status == 'active':
            booking.status = 'cancelled'
            booking.save()
            
            # Tạo thông báo hủy phòng
            Notification.objects.create(
                user=request.user,
                type='booking',
                title='Hủy đặt phòng thành công',
                message=f'Bạn đã hủy đặt phòng {booking.pod.pod_name} từ {booking.start_date} đến {booking.end_date}'
            )
            
            messages.success(request, 'Hủy đặt phòng thành công!')
        else:
            messages.error(request, 'Không thể hủy đặt phòng này!')
    except Exception as e:
        messages.error(request, 'Đã xảy ra lỗi khi hủy đặt phòng!')
    
    return redirect('booking_history')

def get_pod(request, uid):
    try:
        pod = Pod.objects.get(uid=uid)
        today = date.today().strftime('%Y-%m-%d')
        
        # Lấy số giờ từ cả GET và POST
        if request.method == 'POST':
            hours = int(request.POST.get('hours', 1))
        else:
            hours = int(request.GET.get('hours', 1))
        
        # Tính tổng tiền
        total_amount = pod.pod_price * hours
        
        context = {
            'pod': pod,
            'today': today,
            'available_rooms': pod.room_count,
            'total_amount': total_amount,
            'hours': hours
        }
        
        return render(request, 'home/pod.html', context)
        
    except Pod.DoesNotExist:
        messages.error(request, 'Không tìm thấy khách sạn')
        return redirect('index')

def pod_detail(request, pod_id):
    try:
        pod = Pod.objects.get(id=pod_id)
        # Debug: In ra đường dẫn ảnh
        for image in pod.pod_images.all():
            print(f"Image URL: {image.images.url}")
            print(f"Image Path: {image.images.path}")
        context = {
            'pod': pod,
            'pod_images': pod.pod_images.all()  # Lấy tất cả hình ảnh của khách sạn
        }
        return render(request, 'home/pod.html', context)
    except Pod.DoesNotExist:
        return redirect('home')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            user.email = request.POST.get('email', '')
            user.save()

            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            profile.save()

            # Tạo thông báo cập nhật thông tin
            Notification.objects.create(
                user=user,
                type='update',
                title='Cập nhật thông tin thành công',
                message='Thông tin cá nhân của bạn đã được cập nhật'
            )

            messages.success(request, 'Cập nhật thông tin thành công')
        except Exception as e:
            messages.error(request, 'Đã xảy ra lỗi khi cập nhật thông tin')
            
    return redirect('user_profile')

@login_required
def get_notifications(request):
    notifications = request.user.notifications.all()[:10]
    return JsonResponse({
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications],
        'unread_count': request.user.notifications.filter(is_read=False).count()
    })

@login_required
@require_POST
def mark_notification_as_read(request, notification_id):
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def mark_all_notifications_as_read(request):
    try:
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Ví dụ tạo thông báo khi đặt phòng
def create_booking(request, pod_id):
    # ... existing booking code ...
    if booking:
        Notification.create_notification(
            user=request.user,
            type='booking',
            title='Đặt phòng thành công',
            message=f'Bạn đã đặt phòng {pod.pod_name} thành công'
        )

# Thêm thông báo khi đặt phòng thành công
def book_pod(request, uid):
    if request.method == 'POST':
        try:
            pod = Pod.objects.get(uid=uid)
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            check_in_time = request.POST.get('check_in_time', '14:00')
            hours = int(request.POST.get('hours', 1))
            
            # Tạo booking
            booking = PodBooking.objects.create(
                user=request.user,
                pod=pod,
                start_date=start_date,
                end_date=end_date,
                check_in_time=check_in_time,
                hours=hours,
                status='active'
            )
            
            # Tạo thông báo đặt phòng thành công
            Notification.objects.create(
                user=request.user,
                type='booking',
                title='Đặt phòng thành công',
                message=f'Bạn đã đặt phòng {pod.pod_name} thành công từ {start_date} lúc {check_in_time}'
            )
            
            messages.success(request, 'Đặt phòng thành công!')
            return redirect('booking_history')
            
        except Exception as e:
            messages.error(request, 'Đã xảy ra lỗi khi đặt phòng!')
            return redirect('get_pod', uid=uid)
    return redirect('get_pod', uid=uid)

@login_required
@require_POST
def add_review(request, pod_id):
    try:
        pod = get_object_or_404(Pod, uid=pod_id)
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        
        # Kiểm tra xem người dùng đã từng đặt phòng này chưa
        has_booking = PodBooking.objects.filter(
            pod=pod,
            user=request.user,
            status='completed'
        ).exists()
        
        if not has_booking:
            return JsonResponse({
                'status': 'error',
                'message': 'Bạn cần phải đặt và sử dụng phòng trước khi đánh giá'
            }, status=400)
        
        # Kiểm tra xem người dùng đã đánh giá phòng này chưa
        existing_review = Review.objects.filter(pod=pod, user=request.user).first()
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            message = 'Cập nhật đánh giá thành công'
        else:
            Review.objects.create(
                pod=pod,
                user=request.user,
                rating=rating,
                comment=comment
            )
            message = 'Thêm đánh giá thành công'
            
        return JsonResponse({
            'status': 'success',
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def add_feedback(request, pod_id):
    try:
        pod = get_object_or_404(Pod, uid=pod_id)
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        
        if not (1 <= rating <= 5):
            messages.error(request, 'Đánh giá phải từ 1 đến 5 sao')
            return redirect('get_pod', uid=pod_id)
            
        if not comment:
            messages.error(request, 'Vui lòng nhập nhận xét')
            return redirect('get_pod', uid=pod_id)
        
        Feedback.objects.create(
            user=request.user,
            pod=pod,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, 'Cảm ơn bạn đã gửi đánh giá!')
        return redirect('get_pod', uid=pod_id)
        
    except Exception as e:
        messages.error(request, f'Lỗi khi gửi feedback: {str(e)}')
        return redirect('get_pod', uid=pod_id)

def vnpay_payment(request, amount, pod_id=None):
    try:
        # Lấy múi giờ Việt Nam
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vietnam_tz)
        
        # Tạo mã giao dịch
        vnp_TxnRef = current_time.strftime('%Y%m%d%H%M%S') + str(random.randint(100, 999))
        
        # Thời gian tạo giao dịch
        vnp_CreateDate = current_time.strftime('%Y%m%d%H%M%S')
        
        # Thời gian hết hạn (thêm 15 phút)
        expire_time = current_time + timedelta(minutes=15)
        vnp_ExpireDate = expire_time.strftime('%Y%m%d%H%M%S')
        
        # Tạo payload cho VNPay
        vnp = {
            "vnp_Version": "2.1.0",
            "vnp_TmnCode": settings.VNPAY_TMN_CODE,
            "vnp_Amount": int(amount * 100),
            "vnp_Command": "pay",
            "vnp_CreateDate": vnp_CreateDate,
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": get_client_ip(request),
            "vnp_Locale": "vn",
            "vnp_OrderInfo": f"Thanh toan don hang {vnp_TxnRef}",
            "vnp_OrderType": "billpayment",  # Đổi sang billpayment
            "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
            "vnp_TxnRef": vnp_TxnRef,
            "vnp_ExpireDate": vnp_ExpireDate
        }

        # Sắp xếp các tham số theo thứ tự a-z
        vnp_Params = sorted(vnp.items(), key=lambda x: x[0])
        hashdata = "&".join(f"{str(item[0])}={str(item[1])}" for item in vnp_Params)
        
        # Tạo chữ ký
        vnp_SecureHash = hmac.new(
            settings.VNPAY_HASH_SECRET_KEY.encode('utf-8'),
            hashdata.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        # Thêm chữ ký vào payload
        vnp["vnp_SecureHash"] = vnp_SecureHash
        
        # Tạo URL thanh toán
        vnpay_payment_url = f"{settings.VNPAY_PAYMENT_URL}?{urllib.parse.urlencode(vnp)}"
        
        return redirect(vnpay_payment_url)
        
    except Exception as e:
        messages.error(request, 'Có lỗi xảy ra khi tạo thanh toán. Vui lòng thử lại.')
        if pod_id:
            return redirect('pod_detail', pod_id=pod_id)
        return redirect('payment')

def vnpay_return(request):
    try:
        vnp_Params = request.GET
        
        # Kiểm tra trạng thái giao dịch
        vnp_ResponseCode = vnp_Params.get('vnp_ResponseCode')
        
        if vnp_ResponseCode == '24':
            messages.error(request, 'Giao dịch đã quá thời gian chờ thanh toán. Vui lòng thực hiện lại giao dịch.')
            return redirect('payment')  # Chuyển hướng về trang thanh toán
            
        elif vnp_ResponseCode == '00':
            # Giao dịch thành công
            messages.success(request, 'Thanh toán thành công!')
            return redirect('success_page')  # Chuyển hướng đến trang thành công
            
        else:
            # Các trường hợp lỗi khác
            messages.error(request, 'Có lỗi xảy ra trong quá trình thanh toán. Vui lòng thử lại.')
            return redirect('payment')
            
    except Exception as e:
        messages.error(request, 'Có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại.')
        return redirect('payment')

def process_payment(request, pod_id):
    pod = get_object_or_404(Pod, uid=pod_id)
    
    if request.method == 'POST':
        booking_date = request.POST.get('bookingDate')
        check_in_time = request.POST.get('checkInTime')  # Lấy thời gian từ form
        hours = int(request.POST.get('hours', 1))
        
        # Tính tổng tiền
        total_amount = pod.pod_price * hours
        
        # Tạo booking record với thời gian nhận phòng đã chọn
        booking = PodBooking.objects.create(
            user=request.user,
            pod=pod,
            start_date=booking_date,
            end_date=booking_date,
            check_in_time=check_in_time,  # Lưu thời gian đã chọn
            hours=hours,
            total_amount=total_amount,
            booking_type='Pre Paid',
            status='pending'
        )
        
        # Lưu booking_id vào session
        request.session['booking_id'] = str(booking.uid)
        
        # Format ngày để hiển thị
        try:
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_date = booking_date
        
        context = {
            'pod': pod,
            'booking_date': formatted_date,
            'check_in_time': check_in_time,  # Truyền thời gian vào context
            'hours': hours,
            'total_amount': total_amount,
            'booking': booking
        }
        
        return render(request, 'home/payment.html', context)
    
    return redirect('pod_detail', pod_id=pod_id)

def process_payment_method(request):
    if request.method == 'POST':
        booking_id = request.session.get('booking_id')
        if not booking_id:
            messages.error(request, 'Không tìm thấy thông tin đặt phòng!')
            return redirect('home')
            
        try:
            booking = PodBooking.objects.get(uid=booking_id)
            
            # Tạo URL thanh toán VNPay
            payment_url = generate_vnpay_payment_url(
                order_id=str(booking.uid),
                amount=float(booking.total_amount),
                order_desc=f"Thanh toan dat phong ngay {booking.start_date}"
            )
            
            return redirect(payment_url)
            
        except PodBooking.DoesNotExist:
            messages.error(request, 'Không tìm thấy thông tin đặt phòng!')
            return redirect('home')
            
    return redirect('home')

@csrf_exempt  # Thêm decorator này vì VNPay không gửi CSRF token
def payment_return(request):
    # Lấy các tham số từ VNPay trả về
    vnp_ResponseCode = request.GET.get('vnp_ResponseCode')
    vnp_TxnRef = request.GET.get('vnp_TxnRef')
    
    try:
        booking = PodBooking.objects.get(uid=vnp_TxnRef)
        
        if vnp_ResponseCode == "00":
            booking.status = 'completed'
            booking.save()
            
            # Tạo sự kiện trên Google Calendar
            booking.create_calendar_event()
            
            # Tạo thông báo thanh toán thành công
            Notification.objects.create(
                user=booking.user,
                type='booking',
                title='Thanh toán thành công',
                message=f'Bạn đã thanh toán thành công cho đơn đặt phòng {booking.pod.pod_name}'
            )
            
            messages.success(request, 'Thanh toán thành công!')
        else:
            booking.status = 'cancelled'
            booking.save()
            
            # Cập nhật trạng thái sự kiện trên Google Calendar
            booking.update_calendar_event()
            
            # Tạo thông báo hủy thanh toán
            Notification.objects.create(
                user=booking.user,
                type='booking',
                title='Thanh toán không thành công',
                message=f'Đơn đặt phòng {booking.pod.pod_name} đã bị hủy do thanh toán không thành công'
            )
            
            messages.error(request, 'Thanh toán không thành công! Đơn đặt phòng đã bị hủy.')
            
    except PodBooking.DoesNotExist:
        messages.error(request, 'Không tìm thấy thông tin đặt phòng!')
    except Exception as e:
        messages.error(request, f'Đã xảy ra lỗi: {str(e)}')
    
    return redirect('booking_history')

@login_required
def payment_history(request):
    # Thay vì render trang payment_history, chuyển hướng đến booking_history
    return redirect('booking_history')

def payment_success(request):
    booking_id = request.session.get('booking_id')
    if booking_id:
        try:
            # Thay đổi từ Booking sang PodBooking
            booking = PodBooking.objects.get(uid=booking_id)
            booking.status = 'completed'  # Cập nhật trạng thái thành completed
            booking.save()
            
            # Tạo thông báo
            Notification.objects.create(
                user=request.user,
                type='booking',
                title='Thanh toán thành công',
                message=f'Bạn đã thanh toán thành công cho đơn đặt phòng {booking.pod.pod_name}'
            )
            
            # Xóa booking_id khỏi session sau khi đã xử lý
            del request.session['booking_id']
            
            messages.success(request, 'Thanh toán thành công!')
            return redirect('booking_history')
        except PodBooking.DoesNotExist:
            messages.error(request, 'Không tìm thấy thông tin đặt phòng!')
    return redirect('home')

@login_required
def connect_calendar(request):
    """View để bắt đầu quá trình kết nối Google Calendar"""
    try:
        # Tạo thư mục credentials nếu chưa tồn tại
        if not os.path.exists(settings.CREDENTIALS_DIR):
            os.makedirs(settings.CREDENTIALS_DIR)
            
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.GOOGLE_CALENDAR_CREDENTIALS_PATH,
            SCOPES
        )
        # Sử dụng redirect URI từ settings
        flow.redirect_uri = settings.GOOGLE_CALENDAR_REDIRECT_URI
        
        # Thêm tham số để cho phép HTTP trong development
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Luôn yêu cầu người dùng đồng ý
        )
        request.session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        messages.error(request, f'Lỗi khi kết nối Google Calendar: {str(e)}')
        return redirect('user_profile')

@login_required
def calendar_callback(request):
    """Callback view sau khi người dùng authorize với Google"""
    try:
        state = request.session.get('state')
        if not state:
            raise ValueError('Không tìm thấy state trong session')

        flow = InstalledAppFlow.from_client_secrets_file(
            settings.GOOGLE_CALENDAR_CREDENTIALS_PATH,
            SCOPES,
            state=state
        )
        flow.redirect_uri = settings.GOOGLE_CALENDAR_REDIRECT_URI
        
        # Lấy full URL từ request
        authorization_response = request.build_absolute_uri()
        # Chuyển từ http sang https nếu cần
        if settings.DEBUG and authorization_response.startswith('http://'):
            authorization_response = 'https://' + authorization_response[7:]
            
        flow.fetch_token(authorization_response=authorization_response)
        
        # Lưu credentials
        creds = flow.credentials
        with open(settings.GOOGLE_CALENDAR_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
        
        messages.success(request, 'Kết nối Google Calendar thành công!')
    except Exception as e:
        messages.error(request, f'Lỗi khi xử lý callback: {str(e)}')
    
    return redirect('user_profile')

def create_payment(request, pod_id):
    try:
        # Lấy thông tin pod từ database
        pod = get_object_or_404(Pod, id=pod_id)
        
        # Tạo thông tin thanh toán
        amount = pod.price  # Giá của pod
        
        # Chuyển hướng đến trang thanh toán VNPay
        return vnpay_payment(request, amount=amount, pod_id=pod_id)
        
    except Exception as e:
        messages.error(request, 'Có lỗi xảy ra khi tạo thanh toán. Vui lòng thử lại.')
        return redirect('pod_detail', pod_id=pod_id)