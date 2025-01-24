from rest_framework import viewsets
from groups.model.group import photo_group,PhotoGroupImage,GroupMember,CustomGroup,sub_group
from groups.serializers.photo_upload_serializer import PhotoGroupSerializer,PhotoGroupImageSerializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from face.function_call import StandardResultsSetPagination,Global_error_message,check_required_fields
import boto3
import base64
from django.http import Http404
from face.exceptions import CustomError
from face.function_call import ALLOWED_IMAGE_TYPES
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.urls import reverse
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from mimetypes import guess_type
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.decorators import permission_classes
from face.permissions import GroupPermission
import os

User = get_user_model()


class PhotoGroupView(viewsets.ModelViewSet):
    queryset = photo_group.objects.all()
    serializer_class = PhotoGroupSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['photo_name']
    search_fields = ['photo_name']
    
    def get_permissions(self):
        if self.action in ['create']:
            
            self.required_permission = ['add_photo_group']
        elif self.action in ['retrieve','list','access_group_images']:
            
            self.required_permission = ['view_photo_group']
        elif self.action in ['update']:
            
            self.required_permission = ['change_photo_group']
        elif self.action in ['destroy']:
            
            self.required_permission = ['delete_photo_group']
        
        return [IsAuthenticated(), GroupPermission()]
    
    def get_queryset(self):
        return super().get_queryset()
    
    
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
                'current_page':current_page,
                "group":serializer.data['results']
                }}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': False,
                'message': "Something went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
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
        required_fields = ["user", "group"]
        upload_photo_error_message = check_required_fields(required_fields, request.data)
        if upload_photo_error_message:
            return Response({"status": False, "message": upload_photo_error_message}, status=status.HTTP_400_BAD_REQUEST)

        sub_group_id = request.data.get("sub_group")
        group_id = request.data.get("group")

        if sub_group_id:
            try:
                sub_group_instance = sub_group.objects.get(id=sub_group_id)
                request.data["sub_group"] = sub_group_id
                request.data["group"] = sub_group_instance.main_group.id
            except sub_group.DoesNotExist:
                return Response({"status": False, "message": "Invalid sub_group ID."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response({
            "status": True,
            "message": "Photo group with images uploaded successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
        
            
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.serializer_class(
            instance, 
            data=request.data, 
            context={'request': request}, 
            partial=partial
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        
        return Response({
            "status": True,
            "message": "Photo group with images updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            print("instance",instance)
            if instance:
                instance.delete()
            return Response({'status': True, 'message': 'Photo group deleted successfully'}, status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': "data not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':False,
                    'message':Global_error_message,
                    'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance, context={'request': request})
            return Response({'status': True, 'message': 'family data retrieved successfully.', 'data': serializer.data} ,status=status.HTTP_200_OK)
        except Http404:
            return Response({'status': False, 'message': 'Data not found.'},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': Global_error_message, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def access_group_images(self, request, pk=None):
        
        group = get_object_or_404(CustomGroup, pk=pk)
        user_id = request.data.get('user')

      
        is_member = GroupMember.objects.filter(group=group, user=user_id).exists()
        is_creator = group.created_by_id == user_id

      
        images = photo_group.objects.filter(group=group).select_related('user')

        # Serialize and respond
        serializer = self.get_serializer(
            images, 
            many=True,
            context={'request': request, 'from_method': 'all_images'}
        )
        return Response(
            {"status": True, "message": "Image data retrieved successfully", "data": {"user_data": serializer.data}},
            status=status.HTTP_200_OK
        )



class PhotoGroupImageView(viewsets.ModelViewSet):
    queryset = PhotoGroupImage.objects.all()
    serializer_class = PhotoGroupImageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['photo_group']  
    search_fields = ['photo_group__name'] 

    def get_permissions(self):
        if self.action in ['create']:
            self.required_permission = ['add_photogroupimage']
            self.required_groups = ["Group_Admin"]
        elif self.action in ['retrieve','list','list_page']:
            self.required_permission = ['view_photogroupimage']
            self.required_groups = ["Group_Admin", "User"]
        elif self.action in ['update']:
            self.required_permission = ['change_photogroupimage']
            self.required_groups = ["Group_Admin"]
        elif self.action in ['destroy']:
            self.required_permission = ['delete_photogroupimage']
            self.required_groups = ["Group_Admin"]
        elif self.action in ['download_image','serve_single_image']:
            self.required_permission = ['download_image']
            self.required_groups = ["Group_Admin", "User"]
        elif self.action in ['fav_list']:
            self.required_groups = ["Group_Admin"]
            self.required_permission = ['fav_list']
        
        return [IsAuthenticated(), GroupPermission()]
    
    
    # def get_queryset(self):
    #     return super().get_queryset().filter(photo_group__user=self.request.user)
    
    def get_queryset(self):
        return super().get_queryset()
    
    #     user = self.request.user

    #     # If user is Client_Admin, allow all images
    #     if not GroupMember.objects.filter(user=user).exists():
    #         return PhotoGroupImage.objects.all()

    #     # If user is User_Admin, allow only viewing and downloading images
    #     if GroupMember.objects.filter(user=user, role="User").exists() and not GroupMember.objects.filter(user=user, role="Group_Admin").exists():
    #         return PhotoGroupImage.objects.all()  # Assuming User_Admin can see all images

    #     # If user is Group_Admin, restrict access to only their groups
    #     user_groups = GroupMember.objects.filter(user=user, role="Group_Admin").values_list('group', flat=True)
    #     return PhotoGroupImage.objects.filter(group__in=user_groups)
    
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            if not queryset.exists():
                return Response(
                    {"status": False, "message": "No images found!", 'data': []},
                    status=status.HTTP_204_NO_CONTENT
                )
            serializer = self.serializer_class(queryset, many=True, context={'request': request})
            return Response(
                {"status": True, "message": "Images retrieved successfully.", 'data': {"images": serializer.data}},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": False, "message": "Something went wrong!", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def fav_list(self, request, *args, **kwargs):
        group_id = request.data.get("group_id") 
        if not group_id:
            return Response(
                {"status": False, "message": "group_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            queryset = self.filter_queryset(self.get_queryset().filter(photo_group__group__id=group_id, fev=True))
            ordering = request.query_params.get('ordering', None)
            if ordering:
                queryset = queryset.order_by(ordering)
            else:
                queryset =  queryset.annotate(last_modified=Coalesce('updated_at', 'created_at')).order_by('-last_modified') 
                
        except Exception as e:
            return Response(
                    {"status": True, "message": "No images found!"},status=status.HTTP_204_NO_CONTENT)
        try:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                serializer = self.get_paginated_response(serializer.data)
            else:
                serializer = self.serializer_class(queryset, many=True, context={'request': request})
            
            if not queryset.exists():
                return Response(
                    {"status": True, "message": "No images found!"},status=status.HTTP_204_NO_CONTENT)
                
            count = serializer.data['count']
            limit = int(request.GET.get('page_size', 0))
            current_page = int(request.GET.get('page', 0))
            return Response(
                {"status": True, "message": "fev Images retrieved successfully.", 
                 'data': {
                     'total_page': (count + limit - 1),
                     'count': count,
                     'current_page':current_page,
                     "user_data":[{"images": serializer.data['results']}]}},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": False, "message": "Something went wrong!"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
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
            }, status=status.HTTP_400_BAD_REQUimage_2025_01_10T08_58_10_837ZEST)
    
    
    def create(self, request, *args, **kwargs):
        required_fields = ["photo_group", "image2"]
        missing_fields_message = check_required_fields(required_fields, request.data)
        if missing_fields_message:
            return Response(
                {"status": False, "message": missing_fields_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"status": True, "message": "Image uploaded successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"status": False, "message": "Invalid data provided."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.serializer_class(
                instance,
                data=request.data,
                context={'request': request},
                partial=partial
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    {"status": True, "message": "Image updated successfully.", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"status": False, "message": "Invalid data provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': False, 'message': "Something went wrong!", 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance:
                instance.delete()
            return Response(
                {'status': True, 'message': 'Image deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Http404:
            return Response(
                {'status': False, 'message': "Image not found!"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'status': False, 'message': "Something went wrong!", 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance, context={'request': request})
            return Response(
                {'status': True, 'message': 'Image retrieved successfully.', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Http404:
            return Response(
                {'status': False, 'message': 'Image not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'status': False, 'message': "Something went wrong!", 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            


    def download_image(self, request, pk):
        try:
            # Retrieve the image instance
            photo_image = PhotoGroupImage.objects.get(pk=pk)
            if not photo_image.image2:
                return Response(
                    {'status': False, 'message': 'Image not available.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Generate the URL for downloading the image
            download_url_path = reverse('serve-image', kwargs={'pk': pk})  # Generate relative URL path
            download_url = request.build_absolute_uri(download_url_path)  # Create absolute URL

            # Return a success response with the download URL
            return Response(
                {
                    'status': True,
                    'message': 'Download URL generated successfully.',
                    'data': {'download_url': download_url}
                },
                status=status.HTTP_200_OK
            )

        except PhotoGroupImage.DoesNotExist:
            return Response(
                {'status': False, 'message': 'Image not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'status': False, 'message': f'An error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_permissions(self):
        if self.action == 'serve_single_image':
            return [AllowAny()]
        return super().get_permissions()  
    
    @action(detail=True, methods=['get'], url_path='serve-single-image')
    def serve_single_image(self, request, pk=None):
        try:
            # Retrieve the PhotoGroupImage instance
            photo_image = PhotoGroupImage.objects.get(pk=pk)

            # Check if image2 exists
            if not photo_image.image2:
                raise Http404("Image not found.")

            # Extract file name and mime type
            file_name = photo_image.image2.name.split("/")[-1]
            mime_type, _ = guess_type(file_name)

            # Open the file directly
            file = photo_image.image2

            # Prepare the HttpResponse for file download
            response = HttpResponse(file, content_type=mime_type or 'application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'

            return response

        except PhotoGroupImage.DoesNotExist:
            raise Http404("Image not found")