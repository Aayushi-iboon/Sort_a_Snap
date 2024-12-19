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
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, permissions
import random
from django.db.models.functions import Coalesce
from rest_framework import filters
import logging
from face.function_call import check_required_fields
from face.function_call import StandardResultsSetPagination
from django.db import IntegrityError


User = get_user_model()
logging.getLogger(__name__)

class CustomGroupViewSet(viewsets.ModelViewSet):
    queryset = CustomGroup.objects.all()
    serializer_class = CustomGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['name']
    search_fields = ['name']

    # def get_family_photos(self, request, pk=None):
    #     try:
    #         # Get the specific CustomGroup
    #         import ipdb;ipdb.set_trace()
    #         custom_group = self.get_object()

    #         # Retrieve all family members linked to this group
    #         family_members = family.objects.filter(user__in=custom_group.created_by.family_members.all())
            
    #         photo_groups = photo_group.objects.filter(family_members__in=family_members).distinct()
            
    #     except CustomGroup.DoesNotExist:
    #         return Response({"status":False,"error": "CustomGroup not found"}, status=status.HTTP_400_BAD_REQUEST)
    
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


    def list_page(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        ordering = request.query_params.get('ordering', None)
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.annotate(last_modified=Coalesce('updated_at', 'created_at')).order_by('-last_modified')    
        try:
            if not queryset.exists():
                return Response({"status": False, "message": "Data not found!", 'data': []}, status=status.HTTP_204_NO_CONTENT)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                serializer = self.get_paginated_response(serializer.data)
            else:
                serializer = self.serializer_class(queryset, many=True, context={'request': request})

            count = serializer.data['count']
            limit = int(request.GET.get('page_size', 10))
            current_page = int(request.GET.get('page', 1))
            return Response({
                "status": True, 
                "message":"group Data.",
                'data': {'total_page': (count + limit - 1) // limit,
                'count': count,
                'current_page':current_page,"group":serializer.data['results']}
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            

    def create(self, request, *args, **kwargs):
        try:
            required_fields = ["name"]
           
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
                    
                group = serializer.save(created_by=request.user)  
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
        userid = kwargs.get('user')
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
                    "status": True,
                    "message": "No groups found for the user!",
                    # 'data': {"user_data":[]}
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


class JoinGroupView(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer
    permission_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  
        
    def user_verify(self,request):
        try:
            mobile_no = request.data.get('phone_no')
            if not mobile_no:
                return Response({
                    'status': False,
                    'message': 'Mobile number is required to send OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                user_otp.delay(mobile_no)
                return Response({
                    'status': True,
                    'message': f'OTP sent to {mobile_no} successfully.',
                    # 'otp': otp  # Remove this in production; included here for testing purposes
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Failed to send OTP.",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def user_confirm(self, request):
        mobile_no = request.data.get("phone_no")
        otp = request.data.get("otp")   
        try:
            cached_otp = cache.get(f"otp_{mobile_no}")
            if cached_otp == int(otp):
                cache.set(f"verified_{mobile_no}", True, timeout=300)
                try:
                    users=get_user_model().objects.get(phone_no=mobile_no)
                except Exception as e:
                    return Response({
                    'status': True,
                    'message': "User doesn't exist",
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                users.otp_status =True
                users.save()
                return Response({'status':True,'message':'user verified successfully !!',
                }, status=status.HTTP_200_OK)
            
            return Response({"status":True,"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

            
    
    
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
        user = request.user if request.user.is_authenticated else None
        if group_code:
            try:
                group = CustomGroup.objects.get(code=group_code)
            except CustomGroup.DoesNotExist:
                return Response({"status":False,
                                 "detail": "Invalid group code."}, status=status.HTTP_404_NOT_FOUND)
            
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
            {"status":True,"data": serializer.data},
            status=status.HTTP_201_CREATED)
        
        
    def access_user_joined_group(self,request):
        try:
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({
                    'status': False,
                    'message': "User ID is required.",
                }, status=status.HTTP_400_BAD_REQUEST)

            group_memberships = GroupMember.objects.filter(user_id=user_id).select_related('group')
            
            if not group_memberships.exists():
                return Response({
                    "status": True,
                    "message": "The user is not a member of any groups.",
                }, status=status.HTTP_204_NO_CONTENT)
                
            serializer = self.serializer_class(group_memberships, many=True,context={'request': request,'from_method':'group_list'})
            return Response({
                "status": True,
                "message": "User's group memberships retrieved successfully.",
                "data": {"group" : serializer.data}
            }, status=status.HTTP_200_OK)
        
        except IntegrityError as e:
            return Response({
                "status": "error",
                "message": "User is already a member of this group.",
                "status_code": status.HTTP_400_BAD_REQUEST,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                "status": "error",
                "message": "something went wrong ",
                "error": str(e),
            }, status=status.HTTP_400_BAD_REQUEST)


        
        
        
   