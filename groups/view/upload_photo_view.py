from rest_framework import viewsets
from groups.model.group import photo_group,PhotoGroupImage
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
from django.http import HttpResponse
from django.db.models.functions import Coalesce

User = get_user_model()

# class CustomGroupViewSet(viewsets.ModelViewSet):
#     queryset = photo_group.objects.all()
#     serializer_class = photo_serializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [filters.SearchFilter,DjangoFilterBackend]
#     filterset_fields = ['name']
#     search_fields = ['name']

#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())
#         try:
#             if not queryset.exists():
#                 return Response({
#                     "status": False,
#                     "message": "No groups found!",
#                     'data': []
#                 }, status=status.HTTP_204_NO_CONTENT)
                
#             serializer = self.serializer_class(queryset, many=True)
#             return Response({
#                 "status": True,
#                 "message": "Groups retrieved successfully.",
#                 'data': {"user_data":serializer.data} 
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': "Something went wrong!",
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)

#     def create(self, request, *args, **kwargs):
#         try:
#             serializer = self.serializer_class(data=request.data)
#             if serializer.is_valid():
#                 group = serializer.save(created_by=request.user)  # Assuming the logged-in user creates the group
#                 return Response({
#                     'status': True,
#                     'message': 'Group created successfully.',
#                     'id': group.id
#                 }, status=status.HTTP_201_CREATED)
#             return Response({
#                 'status': False,
#                 'message': 'Failed to create group',
#                 'errors': serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': "Something went wrong!",
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)

#     def update(self, request, *args, **kwargs):
#         try:
#             partial = kwargs.pop('partial', True)
#             instance = self.get_object()
#             serializer = self.serializer_class(instance, data=request.data, partial=partial)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response({
#                     'status': True,
#                     'message': 'Group updated successfully.',
#                     'data': serializer.data
#                 }, status=status.HTTP_200_OK)
#             return Response({
#                 'status': False,
#                 'message': 'Failed to update group',
#                 'errors': flatten_errors(serializer.errors)
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': 'An unexpected error occurred while updating group',
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)

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


class PhotoGroupView(viewsets.ModelViewSet):
    queryset = photo_group.objects.all()
    serializer_class = PhotoGroupSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['photo_name']
    search_fields = ['photo_name']
    
    
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
                }
            }, status=status.HTTP_200_OK)
        
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
        # import ipdb;ipdb.set_trace()
        required_fields = ["user","group"]
        upload_photo_error_message = check_required_fields(required_fields, request.data)
        if upload_photo_error_message:
            return Response({"status": False, "message": upload_photo_error_message},status=status.HTTP_400_BAD_REQUEST)
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
        


class PhotoGroupImageView(viewsets.ModelViewSet):
    queryset = PhotoGroupImage.objects.all()
    serializer_class = PhotoGroupImageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['photo_group']  
    search_fields = ['photo_group__name'] 

    def get_queryset(self):
        return super().get_queryset().filter(photo_group__user=self.request.user)

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
            required_fields = ["photo_group"]
            missing_fields_message = check_required_fields(required_fields, request.data)
            if missing_fields_message:
                return Response(
                    {"status": False, "message": missing_fields_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
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
            # Retrieve the instance
            photo_image = PhotoGroupImage.objects.get(pk=pk)
            if not photo_image.image2:
                return Response(
                    {'status': False, 'message': 'Image not available.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = self.serializer_class(photo_image, context={'request': request})

            file = photo_image.image2.open()
            response = HttpResponse(file, content_type='image/jpeg')  # Adjust content type as needed
            response['Content-Disposition'] = f'attachment; filename="{photo_image.image2.name.split("/")[-1]}"'

            return Response(
                {
                    'status': True,
                    'message': 'Image downloaded successfully.',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK,
            )
        except PhotoGroupImage.DoesNotExist:
            raise Http404("Image not found")