import hashlib
import hmac
import urllib.parse
from django.conf import settings
import datetime

def generate_vnpay_payment_url(order_id, amount, order_desc):
    vnp_Url = settings.VNPAY_PAYMENT_URL
    vnp_ReturnUrl = settings.VNPAY_RETURN_URL
    vnp_TmnCode = settings.VNPAY_TMN_CODE
    vnp_HashSecret = settings.VNPAY_HASH_SECRET_KEY
    
    vnp_TxnRef = order_id
    vnp_OrderInfo = order_desc
    vnp_Amount = int(float(amount) * 100)
    vnp_Locale = 'vn'
    vnp_IpAddr = '127.0.0.1'  # Có thể thay đổi theo IP thực tế
    vnp_CreateDate = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    inputData = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": vnp_TmnCode,
        "vnp_Amount": vnp_Amount,
        "vnp_CreateDate": vnp_CreateDate,
        "vnp_CurrCode": "VND",
        "vnp_IpAddr": vnp_IpAddr,
        "vnp_Locale": vnp_Locale,
        "vnp_OrderInfo": vnp_OrderInfo,
        "vnp_OrderType": "billpayment",
        "vnp_ReturnUrl": vnp_ReturnUrl,
        "vnp_TxnRef": vnp_TxnRef,
    }
    
    inputData = sorted(inputData.items())
    hashData = "&".join([f"{urllib.parse.quote_plus(str(item[0]))}={urllib.parse.quote_plus(str(item[1]))}" for item in inputData])
    
    hashValue = hmac.new(
        vnp_HashSecret.encode('utf-8'),
        hashData.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    vnpay_payment_url = vnp_Url + "?" + hashData + "&vnp_SecureHash=" + hashValue
    return vnpay_payment_url 