import random
from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import os

@shared_task
def send_otp(email):
    # import ipdb;ipdb.set_trace()  
    print(f"Sending OTP to: {email}")
    otp = random.randint(100000, 999999)
    print(f"Generated OTP: {otp}")
    cache.set(f"otp_{email}", otp, timeout=300) 
    otp = cache.get(f"otp_{email}")
    print(f"OTP retrieved from cache: {otp}")
    
    subject = "Your OTP Code"
    message = f"Your OTP code is {otp}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    try: 
        print(type(from_email),type(recipient_list))
        send_mail(subject, message, from_email, recipient_list)
        print(f"OTP {otp} sent to {email}")
        print(f"OTP successfully sent to {email}")
    except Exception as e:
        print(f"Failed to send OTP to {email}. Error: {e}")
        return f"Failed to send OTP to the : {str(e)}"
    
    return otp


@shared_task
def user_otp(mobile_no):
    otp = random.randint(10000000, 99999999)
    account_sid =os.getenv("SID")
    auth_token = os.getenv("auth_token")
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            body=f"Your OTP code is {otp}",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=mobile_no,
        )
        cache.set(f"otp_{mobile_no}", otp, timeout=300) 
        otp = cache.get(f"otp_{mobile_no}")
        print(f"OTP {otp} sent to {mobile_no}")
        return f"OTP {otp} successfully sent to {mobile_no}"
    except Exception as e:
        print(f"Failed to send OTP to {mobile_no}. Error: {e}")
        return f"Failed to send OTP to {mobile_no}. Error: {e}"
    