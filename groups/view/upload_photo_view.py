from rest_framework import viewsets
from groups.model.group import photo_group
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
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['photo_name']
    search_fields = ['photo_name']
    
    
    # def get_queryset(self):
    #     return self.queryset.filter(user=self.request.user)
    def get_queryset(self):
        return super().get_queryset()

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