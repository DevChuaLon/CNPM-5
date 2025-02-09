import hashlib
import hmac
import urllib.parse
from django.conf import settings
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle

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

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Lấy service để tương tác với Google Calendar API"""
    creds = None
    token_path = os.path.join(settings.BASE_DIR, 'token.pickle')
    credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds) 