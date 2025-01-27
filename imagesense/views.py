# Create your views here.
# my_app/views.py
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import send_otp,user_otp
from .serializers import OTPSerializer, UserProfileSerializer,LogoutSerializer
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from django.http import Http404
from face.exceptions import CustomError
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import BlackListToken 
import boto3
from django.conf import settings
import concurrent.futures
import multiprocessing
import os
from rest_framework.exceptions import ValidationError
from face.function_call import check_required_fields,StandardResultsSetPagination,flatten_errors
from groups.model.group import CustomGroup,sub_group,PhotoGroupImage,GroupMember
from .tasks import assign_user_to_group
User = get_user_model()

class GenerateOTP(APIView):
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone_no')
            if email:
                user = User.objects.filter(email=email).first()
                if user:
                    if user.otp_status_email:
                        # User is verified by email
                        user.otp_status_email = False
                        user.save()
                        send_otp.delay(email)
                        return Response({
                            "status": True,
                            "message": f"OTP sent to {email} for verification.",
                            "data":None
                        }, status=status.HTTP_200_OK)
                        # refresh = RefreshToken.for_user(user)
                        # return Response({
                        #     "status": True,
                        #     "message": "User already exists and is email-verified!",
                        #     "data": {
                        #         "token": {
                        #             "refresh": str(refresh),
                        #             "access": str(refresh.access_token),
                        #         },
                        #         "email": user.email,
                        #         "edit_profile":user.edit_profile,
                        #         'user_id':user.id,
                        #     }
                        # }, status=status.HTTP_200_OK)
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
                        "message": f"OTP sent to {email}.",
                        "data":None
                    }, status=status.HTTP_200_OK)

            elif phone:
                # Phone-specific flow
                user = User.objects.filter(phone_no=phone).first()
                if user:
                    if user.otp_status:
                        user.otp_status = False
                        user.save()
                        user_otp.delay(phone)
                        return Response({
                            "status": True,
                            "message": f"OTP sent to {phone} for verification.",
                            "data":None
                        }, status=status.HTTP_200_OK)
                        # User is verified by phone
                        # refresh = RefreshToken.for_user(user)
                        # return Response({
                        #     "status": True,
                        #     "message": "User already exists and is phone-verified!",
                        #     "data": {
                        #         "token": {
                        #             "refresh": str(refresh),
                        #             "access": str(refresh.access_token),
                        #         },
                        #         "phone": user.phone_no,
                        #         "edit_profile":user.edit_profile,
                        #         'user_id':user.id,
                        #     }
                        # }, status=status.HTTP_200_OK)
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

        return Response({
        "status": False,
        "message": "Validation failed.",
        "errors": flatten_errors(serializer.errors)  # Include the validation errors
        }, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTP(APIView):
    def post(self, request):
        email = request.data.get("email")
        phone = request.data.get("phone_no")
        otp = request.data.get("otp")
        # import ipdb;ipdb.set_trace()
        if not otp:
            return Response({'status': True,"message": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check email OTP
        if email:
            cached_otp = cache.get(f"otp_{email}")
            if cached_otp == int(otp):
                user, _ = User.objects.get_or_create(email=email)
                user.otp_status_email = True
                user.save()
                
                if user.otp_status_email:  # Check if both email and phone are verified
                    refresh = RefreshToken.for_user(user)
                    assign_user_to_group(user, "Client_Admin")
                    return Response({
                        'status': True,
                        'message': 'Login successfully !!',
                        'data': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                            'email': user.email,
                            'otp_status': user.otp_status_email,
                            'phone_otp_status': user.otp_status,
                            'user_id':user.id,
                            "edit_profile":user.edit_profile,
                            'role': ', '.join([group.name for group in user.groups.all()]),

                        }
                    }, status=status.HTTP_200_OK)
                return Response({'status': True,"message": "Email verified. Please verify your phone number as well."}, status=status.HTTP_200_OK)
        
        # Check phone OTP
        if phone:
            cached_otp = cache.get(f"otp_{phone}")
            # random_suffix_phone = random.randint(1000000000, 9999999999)
            # email = f"guest{random_suffix_phone}@example.com"
            if cached_otp == int(otp):
                if not User.objects.filter(phone_no=phone).exists():
                    user = User.objects.create(phone_no=phone)
                else:
                    user = User.objects.get(phone_no=phone)
                user.otp_status = True
                # user.email = email
                user.save()
                if user.otp_status:
                    refresh = RefreshToken.for_user(user)
                    assign_user_to_group(user, "Client_Admin")
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
                            "edit_profile":user.edit_profile,
                            'user_id':user.id,
                            'role': ', '.join([group.name for group in user.groups.all()]),

                        }
                    }, status=status.HTTP_200_OK)
                return Response({'status': True,"message": "Phone number verified. Please verify your email as well."}, status=status.HTTP_200_OK)
        
        return Response({'status': False,"message": "Invalid OTP or missing email/phone."}, status=status.HTTP_400_BAD_REQUEST)



class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        # Create a mutable copy of request.data
        data = request.data.copy()
        data['user'] = request.user.id
        data['token'] = request.auth.get('jti')
        try:
            users=get_user_model().objects.get(id=data['user'])
            if users:
                users.otp_status = False
                users.otp_status_email = False
                users.save()
            else:
                return Response({'status': False,"message": "Invalid User"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False, "message": "User not found !!"
            },status=status.HTTP_400_BAD_REQUEST)
            
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"status": True, "message": "Logout successfully."})


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    # Initialize AWS Rekognition client
    rekognition_client = boto3.client(
        'rekognition',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY,
        region_name='ap-south-1'  # Replace with your preferred AWS region
    )
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name='ap-south-1'
    )

    def get_queryset(self):
        return super().get_queryset()
    
    def get_user_folder_path(self, user_email):
        """
        Dynamically generates the folder path based on the user's email.
        """
        return f'photos/{user_email}'
        # return os.path.join('media', 'photos', user_email)
    
    def analyze_face(self, request, *args, **kwargs):
        """Compare faces in a reference image with images in the event folder."""
        try:
            s3_bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
            s3_bucket_url = f'https://{s3_bucket_name}.s3.ap-south-1.amazonaws.com'

            if 'image' not in request.data:
                return Response({"status": False, "message": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)

            uploaded_file = request.data['image']
            reference_image_data = uploaded_file.read()

            # Detect faces in the reference image
            response = self.rekognition_client.detect_faces(
                Image={'Bytes': reference_image_data},
                Attributes=['DEFAULT']
            )
            reference_faces = response['FaceDetails']
            if not reference_faces:
                return Response({"status": False, "message": "No faces detected in the reference image."}, status=status.HTTP_400_BAD_REQUEST)

            sub_group_id = request.data.get('sub_group', None)
            group_id = request.data.get('group', None)
            # import ipdb;ipdb.set_trace()
            folder_prefixes = [] 
            user = request.user
            user_email = user.email
            
            if sub_group_id:
                # Fetch sub-group
                subgroup = sub_group.objects.filter(id=sub_group_id).first()
                if not subgroup:
                    return Response({"status": False, "message": "Invalid sub-group ID provided."}, status=status.HTTP_404_NOT_FOUND)

                # Check if user is a member of the main group
                # is_member = GroupMember.objects.filter(group=subgroup.main_group, user=user).exists()
                # if not is_member:
                #     return Response({"status": False, "message": "Access denied. You are not a member of this sub-group's main group."}, status=status.HTTP_403_FORBIDDEN)

                # Fetch images from the specific sub-group
                folder_prefixes.append(f'photos/{user_email}/{subgroup.main_group.name}/{subgroup.name}/')

                # Include the joined members' images from this sub-group
                group_members = GroupMember.objects.filter(group=subgroup.main_group)
                for member in group_members:
                    folder_prefixes.append(f'photos/{member.group.created_by.email}/{subgroup.main_group.name}/{subgroup.name}/')

            elif group_id:
                # Fetch group
                group = CustomGroup.objects.filter(id=group_id).first()
                if not group:
                    return Response({"status": False, "message": "Invalid group ID provided."}, status=status.HTTP_404_NOT_FOUND)

                # Check if user is a member of the group
                # is_member = GroupMember.objects.filter(group=group, user=user).exists()
                # if not is_member:
                #     return Response({"status": False, "message": "Access denied. You are not a member of this group."}, status=status.HTTP_403_FORBIDDEN)

                # Fetch images from the group
                folder_prefixes.append(f'photos/{user_email}/{group.name}/')

                # Include the joined members' images from this group
                group_members = GroupMember.objects.filter(group=group)
                for member in group_members:
                    folder_prefixes.append(f'photos/{member.group.created_by.email}/{group.name}/')

                # Also fetch images from all sub-groups of this group
                sub_groups = sub_group.objects.filter(main_group=group)
                for subgroup in sub_groups:
                    folder_prefixes.append(f'photos/{user_email}/{subgroup.main_group.name}/{subgroup.name}/')

                    # Include the joined members' images from these sub-groups
                    subgroup_members = GroupMember.objects.filter(group=subgroup.main_group)
                    for member in subgroup_members:
                        folder_prefixes.append(f'photos/{member.group.created_by.email}/{subgroup.main_group.name}/{subgroup.name}/')

            else:
                # Fetch images from all groups user created or joined
                created_groups = CustomGroup.objects.filter(created_by=user)
                joined_groups = CustomGroup.objects.filter(groupmember__user=user)

                all_groups = created_groups | joined_groups  # Combine both

                for group in all_groups:
                    folder_prefixes.append(f'photos/{user_email}/{group.name}/')

                    # Include the joined members' images from this group
                    group_members = GroupMember.objects.filter(group=group)
                    for member in group_members:
                        folder_prefixes.append(f'photos/{member.group.created_by.email}/{group.name}/')

                    # Fetch sub-groups of each group
                    sub_groups = sub_group.objects.filter(main_group=group)
                    for subgroup in sub_groups:
                        folder_prefixes.append(f'photos/{user_email}/{subgroup.main_group.name}/{subgroup.name}/')

                        # Include the joined members' images from these sub-groups
                        subgroup_members = GroupMember.objects.filter(group=subgroup.main_group)
                        for member in subgroup_members:
                            folder_prefixes.append(f'photos/{member.group.created_by.email}/{subgroup.main_group.name}/{subgroup.name}/')

            # Step 2: Fetch event image keys from S3 for all the gathered folder prefixes
            event_image_keys = []
            for prefix in folder_prefixes:
                response = self.s3_client.list_objects_v2(Bucket=s3_bucket_name, Prefix=prefix)
                if 'Contents' in response:
                    event_image_keys.extend([
                        obj['Key'] for obj in response['Contents']
                        if obj['Key'].lower().endswith(('png', 'jpg', 'jpeg')) and '_compressed' in obj['Key'].lower()
                    ])

            if not event_image_keys:
                return Response({"status": False, "message": "No event images found for the specified criteria."}, status=status.HTTP_404_NOT_FOUND)

            max_threads = min(16, multiprocessing.cpu_count())
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                matching_images = list(executor.map(
                    lambda key: self.compare_faces_in_image(reference_image_data, s3_bucket_name, key),
                    event_image_keys
                ))

            matching_images = [img for img in matching_images if img is not None]
            images_with_ids = []
            for img in matching_images:
                original_img = img.replace("_compressed", "")
                photo_obj = PhotoGroupImage.objects.filter(image2__icontains=original_img).first()
                image_id = photo_obj.id if photo_obj else f"{hash(img)}"
                if photo_obj:
                    images_with_ids.append({
                        "id":image_id,  # Use database ID
                        "compress_url": f'{s3_bucket_url}/{img}',
                        "image_url": original_img 
                    })
            
            return Response({
                "status": True,
                "message": "Matching images retrieved successfully.",
                "data": {
                    "user_data": [{"images": images_with_ids}]}
            }, status=status.HTTP_200_OK) if images_with_ids else Response({
                "status": False,
                "message": "No matching images found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": False,
                "message": "Something went wrong.",
                "error": f"Error processing the image: {e}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def compare_faces_in_image(self, reference_image_data, bucket_name, event_image_key):
        """Helper method to compare faces in the reference image with an image stored in S3."""
        try:
            # Get image data from S3
            event_image_data = self.s3_client.get_object(Bucket=bucket_name, Key=event_image_key)['Body'].read()

            # Compare the images using Rekognition
            compare_response = self.rekognition_client.compare_faces(
                SourceImage={'Bytes': reference_image_data},
                TargetImage={'Bytes': event_image_data},
                SimilarityThreshold=60
            )

            for match in compare_response['FaceMatches']:
                if match['Similarity'] >= 60:
                    return event_image_key  # Return the key of the matching image
        except Exception as e:
            print(f"Error processing {event_image_key}: {e}")
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
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)
            instance = self.get_object()
            if not instance.is_active:
                return Response({'status': False, 'message': "User is inactive", 'code': "user_inactive"},status=status.HTTP_400_BAD_REQUEST)

            if not partial:
                missing_fields_message = check_required_fields(['email', 'phone_no'], request.data)
                if missing_fields_message:
                    return Response( {'status': False, 'message': missing_fields_message},status=status.HTTP_400_BAD_REQUEST)

            email = request.data.get('email')
            if email and email != instance.email:
                if self.get_queryset().filter(email=email).exists():
                    return Response({'status': False, 'message': "email already exists!"},status=status.HTTP_400_BAD_REQUEST)
            # email_error = validate_unique_email(self.get_queryset(), email, instance)
            # if email_error:
            #     return Response({'status': False, 'message': email_error}, status=status.HTTP_400_BAD_REQUEST)

            phone_no = request.data.get('phone_no')
            if phone_no and phone_no != instance.phone_no:
                if self.get_queryset().filter(phone_no=phone_no).exists():
                    return Response({'status': False, 'message': "phone number already exists!"},status=status.HTTP_400_BAD_REQUEST)

            
            serializer = self.get_serializer(instance, data=request.data, partial=partial) 
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({'status': True, 'message': 'User updated successfully', 'data': {'user':serializer.data}}, status=status.HTTP_200_OK)
        except CustomError as e:
             return Response({
            'status': False,
            'message': "something went ",
            'code': e.code
        }, status=status.HTTP_400_BAD_REQUEST)
    
    
            
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
            return Response({'status': True, 'message': 'User data retrieved successfully.', 'data': serializer.data} ,status=status.HTTP_200_OK)
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
