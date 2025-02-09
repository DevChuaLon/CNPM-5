import hashlib
import hmac
import urllib.parse
from django.conf import settings
import datetime

def generate_vnpay_payment_url(order_id, amount, order_desc, bank_code=None):
    vnp = {}
    vnp['vnp_Version'] = '2.1.0'
    vnp['vnp_Command'] = 'pay'
    vnp['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
    vnp['vnp_Amount'] = int(amount) * 100
    vnp['vnp_CurrCode'] = 'VND'
    vnp['vnp_TxnRef'] = str(order_id)
    vnp['vnp_OrderInfo'] = order_desc
    vnp['vnp_OrderType'] = 'other'
    vnp['vnp_Locale'] = 'vn'
    vnp['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL
    vnp['vnp_IpAddr'] = '127.0.0.1'
    vnp['vnp_CreateDate'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    if bank_code:
        vnp['vnp_BankCode'] = bank_code

    # Sắp xếp các field theo thứ tự a-z
    vnp = sorted(vnp.items())
    
    # Tạo chuỗi ký tự cần ký
    hash_data = '&'.join([f'{urllib.parse.quote_plus(str(item[0]))}={urllib.parse.quote_plus(str(item[1]))}' for item in vnp])
    
    # Tạo chữ ký
    hmac_obj = hmac.new(settings.VNPAY_HASH_SECRET_KEY.encode('utf-8'), 
                        hash_data.encode('utf-8'), 
                        hashlib.sha512).hexdigest()
    
    # Thêm chữ ký vào URL
    payment_url = f"{settings.VNPAY_PAYMENT_URL}?{hash_data}&vnp_SecureHash={hmac_obj}"
    
    return payment_url 