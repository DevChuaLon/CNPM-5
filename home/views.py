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
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        if selected_amenities:
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
        paginator = Paginator(pods, 6)  # 6 khách sạn mỗi trang
        page = request.GET.get('page', 1)
        pods = paginator.get_page(page)
        
        context = {
            'pods': pods,
            'amenities': amenities,
            'selected_amenities': selected_amenities,
            'sort_by': sort_by,
            'search': search,
            'start_date': start_date,
            'end_date': end_date,
            'today': date.today().strftime('%Y-%m-%d')
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
        recent_bookings = bookings.order_by('-created_at')[:5]  # 5 đơn đặt phòng gần nhất
        
        context = {
            'user': request.user,
            'profile': profile,
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'recent_bookings': recent_bookings,
            'today': date.today()
        }
        
        return render(request, 'home/profile.html', context)
        
    except Exception as e:
        messages.error(request, 'Đã xảy ra lỗi khi tải trang profile')
        return redirect('index')

@login_required
def booking_history(request):
    try:
        bookings = PodBooking.objects.filter(
            user=request.user
        ).select_related('pod').order_by('-created_at')
        
        status = request.GET.get('status')
        if status:
            bookings = bookings.filter(status=status)
        
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
        messages.error(request, 'Đã xảy ra lỗi khi tải lịch sử đặt phòng')
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
            
            # Tạo booking
            booking = PodBooking.objects.create(
                user=request.user,
                pod=pod,
                start_date=start_date,
                end_date=end_date,
                status='active'
            )
            
            # Tạo thông báo đặt phòng thành công
            Notification.objects.create(
                user=request.user,
                type='booking',
                title='Đặt phòng thành công',
                message=f'Bạn đã đặt phòng {pod.pod_name} thành công từ {start_date} đến {end_date}'
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
        
        # Validate input
        if not (1 <= rating <= 5):
            messages.error(request, 'Đánh giá phải từ 1 đến 5 sao')
            return redirect('get_pod', uid=pod_id)
            
        if not comment:
            messages.error(request, 'Vui lòng nhập nhận xét')
            return redirect('get_pod', uid=pod_id)
        
        # Lưu feedback vào database
        feedback = Feedback.objects.create(
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