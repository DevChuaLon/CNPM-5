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
        
        qs = HotelBooking.objects.filter(
            hotel__uid=uid,
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
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại')
            return render(request, 'home/signup.html')
        
        user = User.objects.create_user(username=username, password=password)
        messages.success(request, 'Đăng ký thành công')
        return redirect('signin')
    
    return render(request, 'home/signup.html')

def signout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Đăng xuất thành công')
    return redirect('index')

def index(request):
    try:
        # Lấy tất cả khách sạn và sắp xếp theo giá
        hotels = Hotel.objects.all().order_by('hotel_price')
        amenities = Amenities.objects.all()
        
        # Debug: In ra số lượng khách sạn
        print(f"Tổng số khách sạn: {hotels.count()}")
        print(f"Tổng số tiện nghi: {amenities.count()}")
        
        # Xử lý tìm kiếm và lọc
        selected_amenities = request.GET.getlist('selectAmenity')
        sort_by = request.GET.get('sortSelect')
        search = request.GET.get('searchInput')
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        if selected_amenities:
            hotels = hotels.filter(amenities__amenity_name__in=selected_amenities).distinct()
            print(f"Lọc theo tiện nghi: {selected_amenities}")
            print(f"Số khách sạn sau khi lọc: {hotels.count()}")
        
        if search:
            hotels = hotels.filter(
                Q(hotel_name__icontains=search) |
                Q(description__icontains=search)
            )
            print(f"Tìm kiếm với từ khóa: {search}")
            print(f"Số khách sạn sau khi tìm: {hotels.count()}")
        
        if sort_by == 'low_to_high':
            hotels = hotels.order_by('hotel_price')
        elif sort_by == 'high_to_low':
            hotels = hotels.order_by('-hotel_price')
            
        # Phân trang
        paginator = Paginator(hotels, 6)  # 6 khách sạn mỗi trang
        page = request.GET.get('page', 1)
        hotels = paginator.get_page(page)
        
        context = {
            'hotels': hotels,
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
        print(f"Lỗi: {str(e)}")  # Debug log
        messages.error(request, 'Đã xảy ra lỗi khi tải trang chủ')
        return render(request, 'home/index.html', {
            'today': date.today().strftime('%Y-%m-%d')
        })

@login_required
def user_profile(request):
    try:
        user = request.user
        recent_bookings = HotelBooking.objects.filter(
            user=user,
        ).select_related('hotel').order_by('-created_at')[:5]
        
        total_bookings = HotelBooking.objects.filter(user=user).count()
        active_bookings = HotelBooking.objects.filter(user=user, status='active').count()
        
        context = {
            'user': user,
            'recent_bookings': recent_bookings,
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'today': date.today().strftime('%Y-%m-%d')
        }
        
        return render(request, 'home/profile.html', context)
        
    except Exception as e:
        messages.error(request, 'Đã xảy ra lỗi khi tải thông tin người dùng')
        return redirect('index')

@login_required
def booking_history(request):
    try:
        bookings = HotelBooking.objects.filter(
            user=request.user
        ).select_related('hotel').order_by('-created_at')
        
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
            'status_choices': HotelBooking._meta.get_field('status').choices
        }
        
        return render(request, 'home/booking_history.html', context)
        
    except Exception as e:
        messages.error(request, 'Đã xảy ra lỗi khi tải lịch sử đặt phòng')
        return redirect('index')

@login_required
def cancel_booking(request, booking_id):
    try:
        booking = get_object_or_404(HotelBooking, uid=booking_id, user=request.user)
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

def get_hotel(request, uid):
    try:
        hotel = Hotel.objects.get(uid=uid)
        today = date.today().strftime('%Y-%m-%d')
        
        if request.method == 'POST':
            if not request.user.is_authenticated:
                return redirect('signin')
                
            start_date = request.POST.get('startDate')
            end_date = request.POST.get('endDate')
            
            if start_date and end_date:
                if check_booking(uid, hotel.room_count, start_date, end_date):
                    HotelBooking.objects.create(
                        hotel=hotel,
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
            'hotel': hotel,
            'today': today
        }
        return render(request, 'home/hotel.html', context)
        
    except Hotel.DoesNotExist:
        messages.error(request, 'Không tìm thấy khách sạn')
        return redirect('index')