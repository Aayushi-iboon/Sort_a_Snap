from rest_framework import viewsets
from groups.model.group import CustomGroup,GroupMember
from groups.serializers.group_serializers import CustomGroupSerializer, GroupMemberSerializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response
from rest_framework import status
from imagesense.tasks import user_otp
from django.core.cache import cache
from face.function_call import flatten_errors
from django.contrib.auth import get_user_model
from face.permissions import GroupPermission
from rest_framework import filters
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework import status, permissions
import random
from rest_framework.decorators import permission_classes
import logging
from face.function_call import check_required_fields
User = get_user_model()
logging.getLogger(__name__)

class CustomGroupViewSet(viewsets.ModelViewSet):
    queryset = CustomGroup.objects.all()
    serializer_class = CustomGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    filterset_fields = ['name']
    search_fields = ['name']

    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            if not queryset.exists():
                return Response({
                    "status": False,
                    "message": "No groups found!",
                    'data': []
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(queryset, many=True)
            return Response({
                "status": True,
                "message": "Groups retrieved successfully.",
                'data': {"user_data":serializer.data} 
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            required_fields = ["name","access"]
           
            group_error_message = check_required_fields(required_fields, request.data)
            if group_error_message:
                return Response({"status": False, "message": group_error_message},status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                group_name = serializer.validated_data.get('name')
                existing_group = CustomGroup.objects.filter(name=group_name, created_by=request.user).first()
                if existing_group:
                    return Response({
                        'status': False,
                        'message': 'A group with this name already exists.',
                        'id': existing_group.id
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                group = serializer.save(created_by=request.user)  # Assuming the logged-in user creates the group
                return Response({
                    'status': True,
                    'message': 'Group created successfully.',
                    'id': group.id,
                    'code':group.code
                }, status=status.HTTP_201_CREATED)
            return Response({
                'status': False,
                'message': 'Failed to create group',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)
            instance = self.get_object()
            serializer = self.serializer_class(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Group updated successfully.',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Failed to update group',
                'errors': flatten_errors(serializer.errors)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An unexpected error occurred while updating group',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance)
            return Response({
                'status': True,
                'message': 'Group data retrieved successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Group not found.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response({
                'status': True,
                'message': 'Group deleted successfully.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error deleting group.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
            
    def userlist(self, request, *args, **kwargs):
        userid = request.data.get('user')
        if userid:
            users=CustomGroup.objects.filter(created_by=userid)
        else:
            return Response({
                'status': False,
                'message': "user is required !!",
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if not users.exists():
                return Response({
                    "status": False,
                    "message": "No groups found for the user!",
                    'data': []
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(users, many=True)
            return Response({
                "status": True,
                "message": "User-specific groups retrieved successfully.",
                'data': {"user_data": serializer.data} 
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# class GroupMemberViewSet(viewsets.ModelViewSet):
#     queryset = GroupMember.objects.all()
#     serializer_class = GroupMemberSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [filters.SearchFilter,DjangoFilterBackend]
#     filterset_fields = ['group__name']
#     search_fields = ['group__name']
    
#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())
#         try:
#             if not queryset.exists():
#                 return Response({
#                     "status": False,
#                     "message": "No members found!",
#                     'data': []
#                 }, status=status.HTTP_204_NO_CONTENT)

#             serializer = self.serializer_class(queryset, many=True,context={'request': request,'from_method': 'list'})
#             return Response({
#                 "status": True,
#                 "message": "Group members retrieved sugenerate-OTP-viewset/cessfully.",
#                 'data': serializer.data
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': "Something went wrong!",
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)
            
    
#     def user_verify(self,request):
#         try:
#             mobile_number = request.data.get('mobile_number')
#             if not mobile_number:
#                 return Response({
#                     'status': False,
#                     'message': 'Mobile number is required to send OTP.'
#                 }, status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 user_otp.delay(mobile_number)
#                 return Response({
#                     'status': True,
#                     'message': f'OTP sent to {mobile_number} successfully.',
#                     # 'otp': otp  # Remove this in production; included here for testing purposes
#                 }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': "Failed to send OTP.",
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)
    
#     def user_confirm(self, request):
#         mobile_number = request.data.get("mobile_number")
#         otp = request.data.get("otp")   
#         cached_otp = cache.get(f"otp_{mobile_number}")
#         if cached_otp == int(otp):
#             cache.set(f"verified_{mobile_number}", True, timeout=300)
#             return Response({'status':True,'message':'user verified successfully !!',
#             }, status=status.HTTP_200_OK)
        
#         return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        
#     # def create(self, request, *args, **kwargs):
#     #     mobile_number = request.data.get("mobile_number")
#     #     # import ipdb;ipdb.set_trace()  
#     #     user_data = request.data.get("user", {})
#     #     # print("==============",user_data)
#     #     if not isinstance(user_data, dict):
#     #         return Response({
#     #             'status': False,
#     #             'message': "The 'user' field must be a dictionary."
#     #         }, status=status.HTTP_400_BAD_REQUEST)

#     #     # Serialize and save data
#     #     print("---------------------1111111111111111111",request.data)
#     #     serializer = self.serializer_class(data=request.data)
#     #     if serializer.is_valid():
#     #         group_member = serializer.save()
#     #         return Response({
#     #             'status': True,
#     #             'message': 'Group member added successfully.',
#     #             'id': group_member.id
#     #         }, status=status.HTTP_201_CREATED)

#     #     return Response({
#     #         'status': False,
#     #         'message': 'Failed to add member to group',
#     #         'errors': flatten_errors(serializer.errors)
#     #     }, status=status.HTTP_400_BAD_REQUEST)



#     def create(self, request, *args, **kwargs):
#         # import ipdb;ipdb.set_trace()
#         data = request.data.get("user")
#         mobile_number = data.get('phone_no', None)
#         is_verified = cache.get(f"verified_{mobile_number}")
#         try:
#             user = User.objects.get(phone_no=mobile_number)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': 'User is not verified'
#             }, status=status.HTTP_403_FORBIDDEN)
            
#         if not user.otp_status:
#             return Response({
#                 'status': False,
#                 'message': 'User is not verified. Please verify with OTP first.'
#             }, status=status.HTTP_403_FORBIDDEN)
            
#         try:
#             # user, created = User.objects.get_or_create(
#             #     phone_no=mobile_number,
#             #     defaults={
#             #         "email": request.data.get("email", ""),
#             #         "first_name": request.data.get("first_name", ""),
#             #         "last_name": request.data.get("last_name", ""),
#             #     }
#             # )
#             # user.otp_status = True
#             # user.save()
#             # group_member_data = request.data.copy()
#             # group_member_data["user_verified"] = True
#             # group_member_data["user"] = user.id 
            
#             serializer = self.serializer_class(data=request.data)
#             if serializer.is_valid():
#                 member = serializer.save()
#                 return Response({
#                     'status': True,
#                     'message': 'Group member added successfully.',
#                     'id': member.id
#                 }, status=status.HTTP_201_CREATED)
#             return Response({
#                 'status': False,
#                 'message': 'Failed to add member to group',
#                 'errors': flatten_errors(serializer.errors)
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': "Something went wrong!",
#                 'error': flatten_errors(str(e))
#             }, status=status.HTTP_400_BAD_REQUEST)
            
#     # if user change thare email and phone after verification then they can't
#     def update(self, request,pk,*args, **kwargs):
#         try:
#             partial = kwargs.pop('partial', True)
#             instance = self.get_object()
#             serializer = self.serializer_class(
#                 instance, 
#                 data=request.data, 
#                 partial=partial, 
#                 context={'request': request,'from_method': 'updates'}
#             )
#             serializer.is_valid(raise_exception=True)
#             serializer.save()
#             return Response({
#                 'status': True,
#                 'message': 'Group member updated successfully.',
#                 'data': serializer.data
#             }, status=status.HTTP_200_OK)
#         except ValidationError as e:
#             return Response({
#                 'status': False,
#                 'message': 'Validation error',
#                 'errors': flatten_errors(e.detail)
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': 'An error occurred',
#                 'errors': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#     def retrieve(self, request, *args, **kwargs):
#         try:
#             instance = self.get_object()
#             serializer = self.serializer_class(instance)
#             return Response({
#                 'status': True,
#                 'message': 'Group data retrieved successfully.',
#                 'data': serializer.data
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': 'Group not found.',
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)

#     def destroy(self, request, *args, **kwargs):
#         try:
#             instance = self.get_object()
#             instance.delete()
#             return Response({
#                 'status': True,
#                 'message': 'Group deleted successfully.'
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': 'Error deleting group.',
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)


class JoinGroupView(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer
    permission_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  
        
    def user_verify(self,request):
        try:
            mobile_number = request.data.get('phone_no')
            if not mobile_number:
                return Response({
                    'status': False,
                    'message': 'Mobile number is required to send OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                user_otp.delay(mobile_number)
                return Response({
                    'status': True,
                    'message': f'OTP sent to {mobile_number} successfully.',
                    # 'otp': otp  # Remove this in production; included here for testing purposes
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Failed to send OTP.",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def user_confirm(self, request):
        mobile_number = request.data.get("phone_no")
        otp = request.data.get("otp")   
        cached_otp = cache.get(f"otp_{mobile_number}")
        if cached_otp == int(otp):
            cache.set(f"verified_{mobile_number}", True, timeout=300)
            users=get_user_model().objects.get(phone_no=mobile_number)
            users.otp_status =True
            users.save()
            return Response({'status':True,'message':'user verified successfully !!',
            }, status=status.HTTP_200_OK)
        
        return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
    
    
    # working only if authenticated
    
    # def join(self,request):
    #     # import ipdb;ipdb.set_trace()  
    #     user_data=request.data.get('user')
    #     phone_no = user_data.get('phone_no')
    #     group_code = user_data.get('code')  
    #     user = request.user if request.user.is_authenticated else None  
    #     if group_code:
    #         try:
    #             group = CustomGroup.objects.get(code=group_code)
    #         except CustomGroup.DoesNotExist:
    #             return Response({"detail": "Invalid group code."}, status=status.HTTP_404_NOT_FOUND)
    #     elif phone_no:
    #         try:
    #             user = get_user_model().objects.get(phone_no=phone_no)
    #         except get_user_model().DoesNotExist:
                
    #             random_suffix = random.randint(1000, 9999) 
    #             email = f"guest{random_suffix}@example.com"

    #             if get_user_model().objects.filter(email=email).exists():
    #                 raise ValidationError("Generated email already exists.")
    #             user = get_user_model().objects.create(
    #                 email=email,
    #                 phone_no=phone_no, 
    #             )
    #             user.is_active = True
    #             user.save()
    #         group = CustomGroup.objects.first() 
    #     else:
    #         return Response({"detail": "No code or phone number provided."}, status=status.HTTP_400_BAD_REQUEST)

    #     if GroupMember.objects.filter(group=group, user=user).exists():
    #         return Response({"message": "User is already a member of this group."}, status=status.HTTP_400_BAD_REQUEST)
    #     role = "Member" if user.is_authenticated else "Guest"

    #     group_member = GroupMember.objects.create(group=group, user=user, role=role)
        
    #     serializer = GroupMemberSerializer(group_member)
    #     return Response(
    #         {"data": serializer.data},
    #         status=status.HTTP_201_CREATED)
        
    # not authenticated user still working
    # @permission_classes([permissions.AllowAny])
    
    def get_permissions(self):
        """
        Dynamically assign permissions for specific actions.
        """
        if self.action == 'join':  # Check if the current action is 'join'
            return [permissions.AllowAny()]  # No authentication required
        return super().get_permissions()  
      
    def join(self,request):
        user_data=request.data.get('user')
        phone_no = user_data.get('phone_no')
        group_code = user_data.get('code') 
        # phone_no = request.data.get('phone_no')  # Get phone_no from request
        # group_code = request.data.get('code')  # Get code from request
        # import ipdb;ipdb.set_trace()
        user = request.user if request.user.is_authenticated else None

        if group_code:
            try:
                group = CustomGroup.objects.get(code=group_code)
            except CustomGroup.DoesNotExist:
                return Response({"detail": "Invalid group code."}, status=status.HTTP_404_NOT_FOUND)
            
            if not user:
                random_suffix = random.randint(1000, 9999)  # Random suffix for the email
                random_suffix_phone = random.randint(1000000000, 9999999999)
                email = f"guest{random_suffix}@example.com"
                phone = f"+91{random_suffix_phone}"
                
                # Create a new guest user with the random email
                user = get_user_model().objects.create(
                    email=email,
                    phone_no=phone_no if phone_no else phone,  # Save phone_no if it's provided
                )
                user.is_active = True
                user.save()

        elif phone_no:
            
            try:
                user = get_user_model().objects.get(phone_no=phone_no)
            except get_user_model().DoesNotExist:
               
                random_suffix = random.randint(1000, 9999)  
                email = f"guest{random_suffix}@example.com"

                user = get_user_model().objects.create(
                    email=email,
                    phone_no=phone_no
                )
                user.is_active = True
                user.save()

            group = CustomGroup.objects.first() 

        else:
            return Response({"detail": "No code or phone number provided."}, status=status.HTTP_400_BAD_REQUEST)

        
        if GroupMember.objects.filter(group=group, user=user).exists():
            return Response({"detail": "User is already a member of this group."}, status=status.HTTP_400_BAD_REQUEST)

        role = "Member" if user.is_authenticated else "Guest"
        
        # Create the group member entry
        group_member = GroupMember.objects.create(group=group, user=user, role=role)

        # Serialize and return response
        serializer = GroupMemberSerializer(group_member)
        return Response(
            {"data": serializer.data},
            status=status.HTTP_201_CREATED)
        
        
        
        
        
        
    # def join(self, request):
    #     group_id = request.data.get('group')
    #     email = request.data.get("user", {}).get("email")
    #     phone_no = request.data.get("user", {}).get("phone_no")
    #     try:
    #         group = CustomGroup.objects.get(id=group_id)
    #     except CustomGroup.DoesNotExist:
    #         return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    #     if group.access == 'Private' and not request.user.is_authenticated:
    #         return Response({"detail": "You must be authenticated to join a private group."}, status=status.HTTP_403_FORBIDDEN)

    #     user = None
    #     if group.access == 'public':
    #         if email:
    #             try:
    #                 user = User.objects.get(email=email)
    #             except User.DoesNotExist:
    #                 user = None  

    #         if not user and phone_no:
    #             try:
    #                 user = User.objects.get(phone_no=phone_no)  # Assuming you have a `phone_no` field in your `User` model
    #             except User.DoesNotExist:
    #                 user = None  # No user found by phone number

    #         if not user:
    #             random_values=random.randint(0,10000)
    #             user = User.objects.create(
    #                 email=email if email else "guest"+str(random_values)+"@example.com",  # Use email or default
    #                 phone_no=phone_no if phone_no else "",  # Use phone_no if available
    #             )
    #             user.is_active = True
    #             user.save()

    #         role = "Guest"
        
    #     elif group.access == 'private' and request.user.is_authenticated:
    #         user = request.user
    #         role = "Member"
        
    #     else:
    #         return Response({"detail": "You must be authenticated to join this group."}, status=status.HTTP_403_FORBIDDEN)

    #     if GroupMember.objects.filter(group=group, user=user).exists():
    #         return Response({"detail": "User is already a member of this group."}, status=status.HTTP_400_BAD_REQUEST)

    #     group_member = GroupMember.objects.create(group=group, user=user, role=role)

    #     serializer = GroupMemberSerializer(group_member)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        # except CustomGroup.DoesNotExist:
        #     return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # # If the group is private, check if the user is authenticated
        # print("======================>>",group.name)
        # import ipdb;ipdb.set_trace()    
        # if group.name == 'Private' and not request.user.is_authenticated:
        #     return Response({"detail": "You must be authenticated to join a private group."}, status=status.HTTP_403_FORBIDDEN)
        
        # if group.name == 'Private' and request.user.is_authenticated:
            
        #     if GroupMember.objects.filter(group=group, user=request.user).exists():
        #         return Response({"detail": "You are already a member of this group."}, status=status.HTTP_400_BAD_REQUEST)

        #     group_member = GroupMember.objects.create(group=group, user=request.user, role="Member")
        #     serializer = GroupMemberSerializer(group_member)
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)

      
        # if group.name == 'public':
          
        #     if GroupMember.objects.filter(group=group, user=request.user).exists():
        #         return Response({"detail": "You are already a member of this group."}, status=status.HTTP_400_BAD_REQUEST)
          
        #     group_member = GroupMember.objects.create(group=group, user=request.user, role="Member")
        #     serializer = GroupMemberSerializer(group_member)
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)

        # return Response({"detail": "Invalid group access type."}, status=status.HTTP_400_BAD_REQUEST)