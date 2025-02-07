from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout, login
from django.contrib import messages
from django.contrib.auth.models import User
from . models import *
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, date

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
        today = date.today()
        
        if booking.status != 'active':
            messages.error(request, 'Không thể hủy đặt phòng này vì không còn hoạt động')
        elif booking.start_date <= today:
            messages.error(request, 'Không thể hủy đặt phòng này vì đã quá hạn')
        else:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Đã hủy đặt phòng thành công')
            
        return redirect('booking_history')
        
    except Exception as e:
        messages.error(request, 'Đã xảy ra lỗi khi hủy đặt phòng')
        return redirect('booking_history')

def get_pod(request, uid):
    try:
        pod = Pod.objects.get(uid=uid)
        today = date.today().strftime('%Y-%m-%d')
        
        if request.method == 'POST':
            if not request.user.is_authenticated:
                return redirect('signin')
                
            start_date = request.POST.get('startDate')
            end_date = request.POST.get('endDate')
            
            if start_date and end_date:
                if check_booking(uid, pod.room_count, start_date, end_date):
                    PodBooking.objects.create(
                        pod=pod,
                        user=request.user,
                        start_date=start_date,
                        end_date=end_date,
                        booking_type='Pre Paid',
                        status='active'
                    )
                    messages.success(request, 'Đặt phòng thành công')
                    return redirect('booking_history')
                else:
                    messages.error(request, 'Phòng đã hết trong thời gian này')
            else:
                messages.error(request, 'Vui lòng chọn ngày check-in và check-out')
        
        context = {
            'pod': pod,
            'today': today
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
            # Cập nhật thông tin user
            user = request.user
            user.email = request.POST.get('email', '')
            user.save()

            # Cập nhật hoặc tạo profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            profile.save()

            messages.success(request, 'Cập nhật thông tin thành công')
        except Exception as e:
            messages.error(request, 'Đã xảy ra lỗi khi cập nhật thông tin')
            
    return redirect('user_profile')