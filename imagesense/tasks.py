import random
from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import os
from django.conf import settings
import boto3

# Initialize AWS Rekognition client
rekognition_client = boto3.client(
        'rekognition',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY,
        region_name='ap-south-1'  # Replace with your preferred AWS region
)

reference_image_path = 'C:/Users/DELL/Downloads/highcrop.jpg'  # Replace with your reference image path
local_folder_path = 'C:/Users/DELL/OneDrive - xergamin/Documents/Sort_A_Snap/OneDrive_2024-10-25/resize folder'

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
    

def compare_faces_in_image(reference_image_data, event_image_path):
    """Compare faces in reference image and event image, return matching image path if similarity > 60."""
    try:
        with open(event_image_path, 'rb') as image_file:
            event_image_data = image_file.read()

        compare_response = rekognition_client.compare_faces(
            SourceImage={'Bytes': reference_image_data},
            TargetImage={'Bytes': event_image_data},
            SimilarityThreshold=60
        )

        for match in compare_response['FaceMatches']:
            if match['Similarity'] >= 60:
                return event_image_path
    except Exception as e:
        print(f"Error processing {event_image_path}: {e}")
        return None
