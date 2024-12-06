# Create your views here.
# my_app/views.py
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import send_otp,user_otp
from .serializers import OTPSerializer, UserProfileSerializer
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from django.http import Http404
from face.exceptions import CustomError
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import BlackListedToken 
import boto3
from django.conf import settings
import concurrent.futures
import os
from rest_framework.exceptions import ValidationError
from face.function_call import validate_unique_email,check_required_fields


User = get_user_model()

class GenerateOTP(APIView):
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone_no')
        #     if email:
        #         user_with_email = User.objects.filter(email=email).first()
        #         if user_with_email:
        #             return Response({
        #                 "message": "A user with this email already exists."
        #             }, status=status.HTTP_400_BAD_REQUEST)

        # # Check if a phone number is provided and if a user with that phone number already exists
        #     if phone:
        #         user_with_phone = User.objects.filter(phone_no=phone).first()
        #         if user_with_phone:
        #             return Response({
        #                 "message": "A user with this phone number already exists."
        #             }, status=status.HTTP_400_BAD_REQUEST)
        
            if email:
                # Email-specific flow
                user = User.objects.filter(email=email).first()
                if user:
                    if user.otp_status_email:
                        # User is verified by email
                        refresh = RefreshToken.for_user(user)
                        return Response({
                            "message": "User already exists and is email-verified!",
                            "data": {
                                "token": {
                                    "refresh": str(refresh),
                                    "access": str(refresh.access_token),
                                },
                                "status": True,
                                "email": user.email,
                                "otp_status":user.otp_status_email
                            }
                        }, status=status.HTTP_200_OK)
                    else:
                        # Resend email OTP
                        send_otp.delay(email)
                        return Response({
                            "status": True,
                            "message": f"OTP sent to {email} for verification.",
                            "data":None
                        }, status=status.HTTP_200_OK)
                else:
                    # New user: Send email OTP
                    send_otp.delay(email)
                    return Response({
                        "status": True,
                        "message": f"OTP sent to {email}."
                    }, status=status.HTTP_200_OK)

            elif phone:
                # Phone-specific flow
                user = User.objects.filter(phone_no=phone).first()
                if user:
                    if user.otp_status:
                        # User is verified by phone
                        refresh = RefreshToken.for_user(user)
                        return Response({
                            "message": "User already exists and is phone-verified!",
                            "data": {
                                "token": {
                                    "refresh": str(refresh),
                                    "access": str(refresh.access_token),
                                },
                                "status": True,
                                "phone": user.phone_no,
                                "otp_status":user.otp_status
                            }
                        }, status=status.HTTP_200_OK)
                    else:
                        # Resend phone OTP
                        user_otp.delay(phone)
                        return Response({
                            "status": True,
                            "message": f"OTP sent to {phone} for verification.",
                            "data":None
                        }, status=status.HTTP_200_OK)
                else:
                    # New user: Send phone OTP
                    user_otp.delay(phone)
                    return Response({
                        "status": True,
                        "message": f"OTP sent to {phone}.",
                        "data":None
                    }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTP(APIView):
    def post(self, request):
        email = request.data.get("email")
        phone = request.data.get("phone_no")
        otp = request.data.get("otp")
        # import ipdb;ipdb.set_trace()
        if not otp:
            return Response({"message": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check email OTP
        if email:
            cached_otp = cache.get(f"otp_{email}")
            if cached_otp == int(otp):
                user, _ = User.objects.get_or_create(email=email)
                user.otp_status_email = True
                user.save()
                
                if user.otp_status_email:  # Check if both email and phone are verified
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': True,
                        'message': 'Login successfully !!',
                        'data': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                            'email': user.email,
                            'otp_status': user.otp_status_email,
                            'phone_otp_status': user.otp_status,
                            'user_id':user.id
                        }
                    }, status=status.HTTP_200_OK)
                return Response({"message": "Email verified. Please verify your phone number as well."}, status=status.HTTP_200_OK)
        
        # Check phone OTP
        if phone:
            cached_otp = cache.get(f"otp_{phone}")
            if cached_otp == int(otp):
                user, _ = User.objects.get_or_create(phone_no=phone)
                user.otp_status = True
                user.save()
                
                if user.otp_status:  # Check if both email and phone are verified
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': True,
                        'message': 'Login successfully !!',
                        'data': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                            'email': user.email,
                            'phone': user.phone_no,
                            'otp_status': user.otp_status_email,
                            'phone_otp_status': user.otp_status,
                        }
                    }, status=status.HTTP_200_OK)
                return Response({"message": "Phone number verified. Please verify your email as well."}, status=status.HTTP_200_OK)
        
        return Response({"message": "Invalid OTP or missing email/phone."}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def logout(self, request, *args, **kwargs):
        try:
            import ipdb;ipdb.set_trace()
            access_token = request.headers.get('Authorization')
            if access_token is None or not access_token.startswith('Bearer '):
                return Response({
                    'status': False,
                    'message': 'Access token is missing or invalid'
                }, status=status.HTTP_400_BAD_REQUEST)

            access_token = access_token.split(' ')[1]  
            try:
                token = AccessToken(access_token)
                cache.set(f'blacklisted_{access_token}', True, timeout=token.lifetime.total_seconds())
                user = request.user 
                BlackListedToken.objects.create(token=access_token, user=user)
                
                return Response({
                    'status': True,
                    'message': 'User logged out successfully'
                }, status=status.HTTP_200_OK)
            except TokenError:
                return Response({
                    'status': False,
                    'message': 'Token is invalid or expired'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    # Initialize AWS Rekognition client
    rekognition_client = boto3.client(
        'rekognition',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY,
        region_name='ap-south-1'  # Replace with your preferred AWS region
    )

    # Define paths
    # reference_image_path = 'C:/Users/DELL/Downloads/highcrop.jpg'  # Replace with your reference image path
    local_folder_path = 'media/photos/nikam@example.com'  # Replace with your local folder path
    # user_email = request.user.email
    #     if not user_email:
    #         return Response({"error": "User email not found."}, status=400)
    # local_folder_path = self.get_user_folder_path(user_email)
    def get_queryset(self):
        return super().get_queryset()
    
    def get_user_folder_path(self, user_email):
        """
        Dynamically generates the folder path based on the user's email.
        """
        return os.path.join('media', 'photos', user_email)
    
    def analyze_face(self, request, *args, **kwargs):
        """Compare faces in a reference image with images in the event folder."""
        if 'image' not in request.data:
            return Response({"status": False, "message":"Something went wrong!","error":str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        if len(request.FILES) > settings.DATA_UPLOAD_MAX_NUMBER_FILES:
            raise ValidationError(f"Cannot upload more than {settings.DATA_UPLOAD_MAX_NUMBER_FILES} files at once.")
       
        uploaded_file = request.data['image']
        reference_image_data = uploaded_file.read()

        try:
           
            response = self.rekognition_client.detect_faces(
                Image={'Bytes': reference_image_data},
                Attributes=['DEFAULT']
            )

            reference_faces = response['FaceDetails']
            if not reference_faces:
                return Response({"status": False, "message": "No faces detected in the reference image."}, status=status.HTTP_400_BAD_REQUEST)

            
            event_image_paths = [os.path.join(self.local_folder_path, img) for img in os.listdir(self.local_folder_path) if img.lower().endswith(('png', 'jpg', 'jpeg'))]

          
            max_threads = 16
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                matching_images = list(executor.map(lambda path: self.compare_faces_in_image(reference_image_data, path), event_image_paths))

            # Filter out None values (no match found)
            matching_images = [img for img in matching_images if img is not None]
            if matching_images:
                return Response({ "status": True, "message": "Photos retrieved successfully.","data": {"images":matching_images}}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "message": "No matching faces found in the event images."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"status": False, "message":"Something went wrong!","error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def compare_faces_in_image(self, reference_image_data, event_image_path):
        """Helper method to compare faces in reference image with an event image."""
        try:
            with open(event_image_path, 'rb') as image_file:
                event_image_data = image_file.read()

            compare_response = self.rekognition_client.compare_faces(
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


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "No photos found!",
                    'data': []
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(queryset, many=True)
            return Response({
                "status": True,
                "message": "Photos retrieved successfully.",
                'data': {"photos": serializer.data}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({
                "status": True,
                "message": "Photos upload successfully.",
                'data': serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            if not instance.is_active:
                return Response({'status': False, 'message': "User is inactive", 'code': "user_inactive"},status=status.HTTP_400_BAD_REQUEST)

            if not partial:
                missing_fields_message = check_required_fields(['email', 'phone_no'], request.data)
                if missing_fields_message:
                    return Response( {'status': False, 'message': missing_fields_message},status=status.HTTP_400_BAD_REQUEST)

            email = request.data.get('email')
            email_error = validate_unique_email(self.get_queryset(), email, instance)
            if email_error:
                return Response({'status': False, 'message': email_error}, status=status.HTTP_400_BAD_REQUEST)

            phone_no = request.data.get('phone_no')
            if phone_no and phone_no != instance.phone_no:
                if self.get_queryset().filter(phone_no=phone_no).exists():
                    return Response({'status': False, 'message': "This phone number already exists!"},status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'status': True, 'message': 'User updated successfully', 'data': {'user': serializer.data}},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": False, "message": "Something went wrong!", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            print("instance",instance)
            if instance:
                instance.delete()
            return Response({'status': True, 'message': 'User deleted successfully'}, status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': "User not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':"Something went wrong !!",
                    'error':str(e)},status=status.HTTP_400_BAD_REQUEST)


    def retrieve(self, request, *args, **kwargs):
        # import ipdb;ipdb.set_trace()
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance, context={'request': request})
            return Response({'status': True, 'message': 'User data retrieved successfully.', 'data': {"user":serializer.data}} ,status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': 'Data not found.'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': "something went wrong ! ", 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
    def verified_user_retrived(self, request, *args, **kwargs):
        try:
            phone_numbers = request.data.get("phone_no", [])
            
            if not phone_numbers or not isinstance(phone_numbers, list):
                return Response({
                    "status": False,
                    "message": "Invalid or missing phone_numbers list.",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            users = User.objects.filter(phone_no__in=phone_numbers, otp_status=True)
            
            if not users.exists():
                return Response({
                    "status": False,
                    "message": "No users found with otp_status True.",
                    "data": []
                }, status=status.HTTP_204_NO_CONTENT)
            
            serializer = UserProfileSerializer(users, many=True, context={"request": request})
            return Response({
                "status": True,
                "message": "Users with otp_status True.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": False,
                "message": "Something went wrong!",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST) 
        
# class GenerateOTP(APIView):
#     def post(self, request):
#         serializer = OTPSerializer(data=request.data)
#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             print("--->",email)
#             res=send_otp.delay(email)  # Call the task asynchronously
#             print("===>>",res)
#             return Response({"message": f"OTP sent successfully to {email}"},status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# def create(self, request, *args, **kwargs):
    #     try:update
    #         email = request.data.get('email')
    #         # if CustomUser.objects.filter(email=email).exists():
    #         #     return Response({'status': False, 'message': 'Email already exists'},
    #         #                 status=status.HTTP_400_BAD_REQUEST)
    #         # username = request.data.get('username')
    #         # if CustomUser.objects.filter(username=username).exists():
    #         #     return Response({'status': False, 'message': 'username already exists'},
    #         #                 status=status.HTTP_400_BAD_REQUEST)
                
    #         serializer = self.get_serializer(data=request.data)
    #         serializer.is_valid(raise_exception=True)
    #         self.perform_create(serializer)
    #         return Response({'status': True, 'message': 'User created successfully'},
    #                         status=status.HTTP_201_CREATED)
    #     except Exception as e:
    #         return Response({'status': False, 'message': 'Failed to create User', 'error': str(e)},
    #                         status=status.HTTP_400_BAD_REQUEST)
    
    
    
    # def update(self, request, *args, **kwargs):
    #     try:
    #         partial = kwargs.pop('partial', True)
    #         instance = self.get_object()
    #         serializer = self.serializer_class(instance, data=request.data, partial=partial,context={'request': request})
            
    #         if serializer.is_valid():
    #             serializer.save()
    #             return Response({'status': True, 'message': 'User updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
            
    #         error_message = "wrong"
    #         return Response({'status': False, 'message': 'Failed to update User', 'errors': error_message}, status=status.HTTP_400_BAD_REQUEST)
    #     except Exception as e:
    #         return Response({'status':False,
    #                 'message':"Might be some error !! ",
    #                 'error':str(e)},status=status.HTTP_400_BAD_REQUEST)


# class EditProfile(APIView):
#     permission_classes = [IsAuthenticated]

#     def put(self, request):
#         user = request.user  # Access the authenticated user
#         serializer = UserProfileSerializer(user, data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Profile updated successfully"}, status=200)
        
#         return Response(serializer.errors, status=400)
